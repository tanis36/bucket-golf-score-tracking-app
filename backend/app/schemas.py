from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional

class PlayerBase(BaseModel):
    name: str

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    id: int
    career_wins: int
    
    class Config:
        orm_mode = True

class RoundBase(BaseModel):
    date: date
    round_number: int
    
class RoundCreate(RoundBase):
    pass
    
class Round(RoundBase):
    id: int
    
    class Config:
        orm_mode = True
        
class ScoreEntryBase(BaseModel):
    player_id: int
    hole_number: int
    strokes: int
    bucket_made: bool
    
class ScoreEntryCreate(ScoreEntryBase):
    pass

class ScoreEntry(ScoreEntryBase):
    id: int
    round_id: int
    
    class Config:
        orm_mode = True
        
class LeaderboardEntry(BaseModel):
    player_id: int
    player_name: str
    total_effective_strokes: int
    total_relative_to_par: int
    rank: int
    career_wins: int
        
class RoundResult(BaseModel):
    round_id: int
    winner_player_id: int
    winner_name: str
    timestamp: datetime
    
class CareerStats(BaseModel):
    player_id: int
    player_name: str
    career_wins: int
    total_rounds: int
    win_percentage: float
    best_total_relative_to_par: Optional[int]
    average_total_relative_to_par: Optional[int]