from fastapi import APIRouter, Request, Form, Depends, Body
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from app.models import TournamentSessionLocal, TeamSessionLocal, Tournament, Team
import logging

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

def get_tournament_db():
    db = TournamentSessionLocal()
    try: yield db
    finally: db.close()

def get_team_db():
    db = TeamSessionLocal()
    try: yield db
    finally: db.close()

# --- HELPER: Get User ID from Cookie ---
def get_current_user(request: Request):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    return int(user_id)

@router.get("/create_tournament")
def create_tournament_get(request: Request):
    if not get_current_user(request): return RedirectResponse("/sign") # Protect Route
    return templates.TemplateResponse(request, "create_tournament.html", {"request": request})

@router.get("/format")
def format_selection_page(request: Request):
    if not get_current_user(request): return RedirectResponse("/sign") # Protect Route
    return templates.TemplateResponse(request, "format.html", {"request": request})

@router.post("/tournament/format")
def select_format(request: Request, format: str = Form(...), teams: int | None = Form(None), db: Session = Depends(get_tournament_db)):
    user_id = get_current_user(request)
    if not user_id:
        return RedirectResponse("/sign", status_code=303)

    if teams is None:
        return templates.TemplateResponse(request, f"{format}.html", {"request": request, "show_teams": True, "category": format})
    
    # USE THE COOKIE ID, NOT 1
    tournament = Tournament(category=format, teams=teams, user_id=user_id)
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    
    return RedirectResponse(url=f"/tournament/{tournament.id}/table", status_code=303)

@router.get("/my_tournaments")
def my_tournaments_page(request: Request, db: Session = Depends(get_tournament_db)):
    user_id = get_current_user(request)
    if not user_id:
        return RedirectResponse("/sign") # Redirect to login if no cookie

    # FILTER BY USER ID (Only show Fardin's if Fardin is logged in)
    tournaments = db.query(Tournament).filter(Tournament.user_id == user_id).all()
    
    return templates.TemplateResponse(request, "my_tournaments.html", {"request": request, "tournaments": tournaments})

# ... (Keep view_tournament_table, add_team, update_teams, delete_team, next_round, delete_tourn AS IS) ...
# ... (They rely on tournament_id, which is already specific, so they don't need major changes) ...
# Just make sure to include the REST of the file I gave you previously below this line:

@router.get("/tournament/{tournament_id}/table")
def view_tournament_table(request: Request, 
                          tournament_id: int, 
                          mode: str | None = None,
                          db_tourn: Session = Depends(get_tournament_db), 
                          db_team: Session = Depends(get_team_db)):
    
    tournament = db_tourn.query(Tournament).filter(Tournament.id == tournament_id).first()
    
    user_id = get_current_user(request)
    
    # Editable if: Mode is NOT viewer AND the logged-in user owns the tournament
    is_editable = False
    if mode != 'viewer' and user_id is not None and tournament is not None and int(getattr(tournament, "user_id")) == user_id:
        is_editable = True
        
    if not tournament:
        return templates.TemplateResponse(request, "table.html", {"request": request, "error": "Not Found", "is_editable": False})
    
    teams = db_team.query(Team).filter(Team.tournament_id == tournament_id)\
                   .order_by(Team.pts.desc(), Team.gd.desc(), Team.gf.desc()).all()
    
    return templates.TemplateResponse(request, "table.html", {
        "request": request,
        "tournament_id": tournament_id,
        "category": str(getattr(tournament, "category")),
        "teams": teams,
        "is_editable": is_editable
    })

# ... (Paste the API Routes: add_team_table, update_teams, etc. here from the previous file) ...
# ... (Make sure to include the API routes exactly as they were) ...

@router.post("/add_team_table")
def add_team_table(team_data: dict = Body(...), 
                   db_tourn: Session = Depends(get_tournament_db),
                   db_team: Session = Depends(get_team_db)):
    try:
        t_id = int(team_data['tournament_id'])
        tournament = db_tourn.query(Tournament).filter(Tournament.id == t_id).first()
        current_count = db_team.query(Team).filter(Team.tournament_id == t_id).count()
        if tournament is not None and current_count >= int(getattr(tournament, "teams")):
             return JSONResponse(status_code=400, content={"message": "Max teams reached."})
        win, lose, draw = int(team_data['win']), int(team_data['lose']), int(team_data['draw'])
        gf, ga = int(team_data['gf']), int(team_data['ga'])
        if win < 0 or lose < 0 or draw < 0 or gf < 0 or ga < 0:
            return JSONResponse(status_code=400, content={"message": "Stats cannot be negative."})
        new_team = Team(
            tournament_id=t_id, category=str(getattr(tournament, "category")) if tournament is not None else "unknown", user_id=1,
            name=team_data['name'], win=win, lose=lose, draw=draw, gf=gf, ga=ga,
            gd=gf - ga, pts=(win * 3) + draw
        )
        db_team.add(new_team)
        db_team.commit()
        return {"message": "Success"}
    except Exception as e: return JSONResponse(status_code=500, content={"message": str(e)})

@router.post("/update_teams")
def update_teams_api(teams: list[dict] = Body(...), db: Session = Depends(get_team_db)):
    try:
        for t in teams:
            team_db = db.query(Team).filter(Team.id == t['teamId']).first()
            if team_db:
                win, lose, draw = int(t['win']), int(t['lose']), int(t['draw'])
                gf, ga = int(t['gf']), int(t['ga'])
                if win < 0 or lose < 0 or draw < 0 or gf < 0 or ga < 0:
                     return JSONResponse(status_code=400, content={"message": "Negative value detected"})
                setattr(team_db, "name", t['name'])
                setattr(team_db, "win", win)
                setattr(team_db, "lose", lose)
                setattr(team_db, "draw", draw)
                setattr(team_db, "gf", gf)
                setattr(team_db, "ga", ga)
                setattr(team_db, "gd", gf - ga)
                setattr(team_db, "pts", (win * 3) + draw)
        db.commit()
        return {"message": "Updated"}
    except Exception as e: db.rollback(); return JSONResponse(status_code=500, content={"message": str(e)})

@router.post("/delete_team")
def delete_team_api(payload: dict = Body(...), db: Session = Depends(get_team_db)):
    try:
        team = db.query(Team).filter(Team.id == payload.get("team_id")).first()
        if team: db.delete(team); db.commit(); return {"message": "Deleted"}
        return JSONResponse(status_code=404, content={"message": "Not found"})
    except Exception as e: return JSONResponse(status_code=500, content={"message": str(e)})

@router.post("/promote_next_round")
def promote_next_round(payload: dict = Body(...), db_tourn: Session = Depends(get_tournament_db), db_team: Session = Depends(get_team_db)):
    try:
        tournament_id_raw = payload.get("tournament_id")
        promote_count_raw = payload.get("promote_count")
        if tournament_id_raw is None or promote_count_raw is None:
            return JSONResponse(status_code=400, content={"message": "Missing tournament_id or promote_count"})
        tournament_id = int(tournament_id_raw)
        promote_count = int(promote_count_raw)

        current_tourn = db_tourn.query(Tournament).filter(Tournament.id == tournament_id).first()
        if not current_tourn: return JSONResponse(status_code=404, content={"message": "Tournament not found"})
        top_teams = db_team.query(Team).filter(Team.tournament_id == current_tourn.id).order_by(Team.pts.desc(), Team.gd.desc(), Team.gf.desc()).limit(promote_count).all()
        if len(top_teams) < promote_count: return JSONResponse(status_code=400, content={"message": "Not enough teams."})
        new_tourn = Tournament(category=f"{current_tourn.category} - Next Round", teams=promote_count, user_id=current_tourn.user_id)
        db_tourn.add(new_tourn); db_tourn.commit(); db_tourn.refresh(new_tourn)
        for old in top_teams: db_team.add(Team(tournament_id=new_tourn.id, category=new_tourn.category, user_id=new_tourn.user_id, name=old.name, win=0, lose=0, draw=0, gf=0, ga=0, gd=0, pts=0))
        db_team.commit()
        return {"next_url": f"/tournament/{new_tourn.id}/table"}
    except Exception as e: db_tourn.rollback(); db_team.rollback(); return JSONResponse(status_code=500, content={"message": str(e)})

@router.post("/delete_tournament")
def delete_tournament(payload: dict = Body(...), db_tourn: Session = Depends(get_tournament_db), db_team: Session = Depends(get_team_db)):
    try:
        tournament_id_raw = payload.get("tournament_id")
        if tournament_id_raw is None:
            return JSONResponse(status_code=400, content={"message": "Missing tournament_id"})
        t_id = int(tournament_id_raw)
        db_team.query(Team).filter(Team.tournament_id == t_id).delete(synchronize_session=False)
        db_team.commit()
        tournament = db_tourn.query(Tournament).filter(Tournament.id == t_id).first()
        if tournament: db_tourn.delete(tournament); db_tourn.commit(); return {"message": "Deleted", "redirect_url": "/my_tournaments"}
        else: return JSONResponse(status_code=404, content={"message": "Not found"})
    except Exception as e: db_team.rollback(); db_tourn.rollback(); return JSONResponse(status_code=500, content={"message": str(e)})