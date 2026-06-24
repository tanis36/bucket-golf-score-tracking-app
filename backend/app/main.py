from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict
from .database import Base, engine
from . import models, schemas, crud
from .deps import get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Bucket Golf API")

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_rounds: Dict[int, List[WebSocket]] = {}
        
    async def connect(self, round_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_rounds.setdefault(round_id, []).append(websocket)
        
    def disconnect(self, round_id: int, websocket: WebSocket):
        if round_id in self.active_rounds:
            self.active_rounds[round_id].remove(websocket)
            
    async def broadcast(self, round_id: int, message: dict):
        for ws in self.active_rounds.get(round_id, []):
            await ws.send_json(message)
            
manager = ConnectionManager()

@app.post("/players", response_model=schemas.Player)
def create_player(player: schemas.PlayerCreate, db: Session = Depends(get_db)):
    return crud.create_player(db, player)

@app.get("/players", response_model=List[schemas.Player])
def list_players(db: Session = Depends(get_db)):
    return crud.get_players(db)

@app.get("/players/{player_id}", response_model=schemas.Player)
def get_player(player_id: int, db: Session = Depends(get_db)):
    p = crud.get_player(db, player_id)
    if not p:
        raise RuntimeError("Player not found")
    return p

@app.get("/players/{player_id}/career", response_model=schemas.CareerStats)
def get_career(player_id: int, db: Session = Depends(get_db)):
    stats = crud.get_career_stats(db, player_id)
    if not stats:
        raise RuntimeError("Player not found")
    return stats

@app.post("/rounds", response_model=schemas.Round)
def create_round(round_in: schemas.RoundCreate, db: Session = Depends(get_db)):
    return crud.create_round(db, round_in)

@app.get("/rounds", response_model=List[schemas.Round])
def list_rounds(date: str, db: Session = Depends(get_db)):
    from datetime import datetime
    d = datetime.fromisoformat(date).date()
    return crud.get_rounds_by_date(db, d)

@app.get("/rounds/{round_id}", response_model=schemas.Round)
def get_round(round_id: int, db: Session = Depends(get_db)):
    r = crud.get_round(db, round_id)
    if not r:
        raise RuntimeError("Round not found")
    return r

@app.post("/rounds/{round_id}/scores", response_model=schemas.ScoreEntry)
async def upsert_score(round_id: int, score_in: schemas.ScoreEntryCreate, db: Session = Depends(get_db)):
    score = crud.upsert_score(db, round_id, score_in)
    leaderboard = crud.compute_leaderboard(db, round_id)
    await manager.broadcast(
        round_id,
        {
            "type": "score_update",
            "round_id": round_id,
            "leaderboard": [entry.model_dump() for entry in leaderboard],
        },
    )
    return score

@app.get("/rounds/{round_id}/scores", response_model=List[schemas.ScoreEntry])
def get_scores(round_id: int, db: Session = Depends(get_db)):
    return crud.get_scores_for_round(db, round_id)

@app.get("/leaderboard/round/{round_id}", response_model=List[schemas.LeaderboardEntry])
def get_leaderboard(round_id: int, db: Session = Depends(get_db)):
    return crud.compute_leaderboard(db, round_id)

@app.post("/rounds/{round_id}/finalize", response_model=schemas.RoundResult)
async def finalize_round(round_id: int, db: Session = Depends(get_db)):
    result = crud.finalize_round(db, round_id)
    if not result:
        raise RuntimeError("Cannot finalize round")
    leaderboard = crud.compute_leaderboard(db, round_id)
    await manager.broadcast(
        round_id,
        {
            "type": "round_finalized",
            "round_id": round_id,
            "leaderboard": [entry.model_dump() for entry in leaderboard],
            "winner": result.model_dump(),
        },
    )
    return result

@app.websocket("/ws/rounds/{round_id}")
async def websocket_endpoint(websocket: WebSocket, round_id: int):
    await manager.connect(round_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(round_id, websocket)