# app/models.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Database URLs ---
USER_DB_URL = "sqlite:///./app/login.db"
TOURNAMENT_DB_URL = "sqlite:///./app/tournament.db"
TEAM_DB_URL = "sqlite:///./app/team.db"

# --- Engines ---
user_engine = create_engine(USER_DB_URL, connect_args={"check_same_thread": False})
tournament_engine = create_engine(TOURNAMENT_DB_URL, connect_args={"check_same_thread": False})
team_engine = create_engine(TEAM_DB_URL, connect_args={"check_same_thread": False})

# --- Session Makers ---
UserSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=user_engine)
TournamentSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=tournament_engine)
TeamSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=team_engine)

# --- Base Classes ---
UserBase = declarative_base()
TournamentBase = declarative_base()
TeamBase = declarative_base()

# --- Models ---

class User(UserBase):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

class Tournament(TournamentBase):
    __tablename__ = "tournaments"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False)
    teams = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=True) 

class Team(TeamBase):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    # Logical references
    tournament_id = Column(Integer, nullable=False)
    category = Column(String, nullable=True)
    user_id = Column(Integer, nullable=True)
    
    name = Column(String, nullable=False)
    # MAKE SURE THESE COLUMNS EXIST IN YOUR FILE:
    win = Column(Integer, default=0)
    lose = Column(Integer, default=0)
    draw = Column(Integer, default=0)
    gf = Column(Integer, default=0)
    ga = Column(Integer, default=0)
    gd = Column(Integer, default=0)
    pts = Column(Integer, default=0)