from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime, timezone

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    career_wins = Column(Integer, default=0)
    
    scores = relationship("ScoreEntry", back_populates="player")
    round_results = relationship("RoundResult", back_populates="winner")
    
class Round(Base):
    __tablename__ = "rounds"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    round_number = Column(Integer)
    
    scores = relationship("ScoreEntry", back_populates="round")
    result = relationship("RoundResult", back_populates="round", uselist=False)

class ScoreEntry(Base):
    __tablename__ = "scores"
    
    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    round_id = Column(Integer, ForeignKey("rounds.id"))
    hole_number = Column(Integer)
    strokes = Column(Integer)
    bucket_made = Column(Boolean, default=False)
    
    player = relationship("Player", back_populates="scores")
    round = relationship("Round", back_populates="scores")

class RoundResult(Base):
    __tablename__ = "round_results"
    
    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"))
    winner_player_id = Column(Integer, ForeignKey("players.id"))
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
    
    round = relationship("Round", back_populates="result")
    winner = relationship("Player", back_populates="round_results")