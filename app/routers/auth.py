from fastapi import APIRouter, Request, Depends, Form, Response # Added Response
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.models import UserSessionLocal, User
from starlette.status import HTTP_303_SEE_OTHER
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

logging.basicConfig(level=logging.INFO)

def get_user_db():
    db = UserSessionLocal()
    try: yield db
    finally: db.close()

@router.get("/sign")
def sign_page(request: Request):
    return templates.TemplateResponse(request, "sign.html", {"request": request})

@router.post("/sign/signup")
def signup(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_user_db)):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return JSONResponse(status_code=400, content={"message": "User account already created."})
    
    new_user = User(email=email, password=password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Return JSON so the popup works
    return JSONResponse(content={
        "message": "Success", 
        "user_id": new_user.id,
        "redirect_url": "/sign" # Send them to login page after signup
    })

@router.post("/sign/login")
def login(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_user_db)):
    user = db.query(User).filter(User.email == email, User.password == password).first()
    
    if user:
        # --- SESSION LOGIC START ---
        # Instead of returning immediately, we create a response object
        response = RedirectResponse("/my_tournaments", status_code=HTTP_303_SEE_OTHER)
        
        # We attach a cookie to the response so the browser remembers the ID
        response.set_cookie(key="user_id", value=str(user.id))
        
        return response
        # --- SESSION LOGIC END ---
    else:
        return templates.TemplateResponse(request, "sign.html", {"request": request, "error": "Invalid credentials."})

# ... (Keep Forgot Password logic the same) ...
@router.post("/sign/forgot")
def forgot_password(request: Request, id: int = Form(...), email: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_user_db)):
    user = db.query(User).filter(User.id == id, User.email == email).first()
    if user:
        setattr(user, "password", new_password)
        db.commit()
        return RedirectResponse("/sign", status_code=HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "sign.html", {"request": request, "error": "User not found."})

# --- NEW: LOGOUT ROUTE ---
@router.get("/logout")
def logout():
    response = RedirectResponse("/sign", status_code=HTTP_303_SEE_OTHER)
    response.delete_cookie("user_id") # Delete the cookie
    return response