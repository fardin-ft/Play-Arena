from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import auth, tournament
from app import models

app = FastAPI()

# Include Routers
app.include_router(auth.router)
app.include_router(tournament.router)

# Mount Static (Optional, create app/static folder if you need CSS/JS files later)
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

# Create Tables for ALL 3 Databases on startup
models.UserBase.metadata.create_all(bind=models.user_engine)
models.TournamentBase.metadata.create_all(bind=models.tournament_engine)
models.TeamBase.metadata.create_all(bind=models.team_engine)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request}, status_code=200)