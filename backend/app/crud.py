from sqlalchemy.orm import Session
from datetime import date
from typing import List, Optional
from . import models, schemas

PAR_PER_HOLE = 3
PAR_PER_ROUND = PAR_PER_HOLE * 9

def create_player(db: Session, player: schemas.PlayerCreate) -> models.Player:
    db_player = models.Player(name=player.name)
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

def get_players(db: Session) -> List[models.Player]:
    return db.query(models.Player).all()

def get_player(db: Session, player_id: int) -> Optional[models.Player]:
    return db.query(models.Player).filter(models.Player.id == player_id).first()

def create_round(db: Session, round_in: schemas.RoundCreate) -> models.Round:
    db_round = models.Round(date=round_in.date, round_number=round_in.round_number)
    db.add(db_round)
    db.commit()
    db.refresh(db_round)
    return db_round

def get_rounds_by_date(db: Session, d: date) -> List[models.Round]:
    return db.query(models.Round).filter(models.Round.date == d).all()

def get_round(db: Session, round_id: int) -> Optional[models.Round]:
    return db.query(models.Round).filter(models.Round.id == round_id).first()

def upsert_score(db: Session, round_id: int, score_in: schemas.ScoreEntryCreate) -> models.ScoreEntry:
    score = (
        db.query(models.ScoreEntry)
        .filter(
            models.ScoreEntry.round_id == round_id,
            models.ScoreEntry.player_id == score_in.player_id,
            models.ScoreEntry.hole_number == score_in.hole_number,
        )
        .first()
    )
    if score is None:
        score = models.ScoreEntry(
            round_id=round_id,
            player_id=score_in.player_id,
            hole_number=score_in.hole_number,
            strokes=score_in.strokes,
            bucket_made=score_in.bucket_made,
        )
        db.add(score)
    else:
        score.strokes = score_in.strokes
        score.bucket_made = score_in.bucket_made
    
    db.commit()
    db.refresh(score)
    return score

def get_scores_for_round(db: Session, round_id: int) -> List[models.ScoreEntry]:
    return db.query(models.ScoreEntry).filter(models.ScoreEntry.round_id == round_id).all()

def compute_leaderboard(db: Session, round_id: int) -> List[schemas.LeaderboardEntry]:
    scores = get_scores_for_round(db, round_id)
    players = {p.id: p for p in get_players(db)}
    
    per_player = {}
    for s in scores:
        eff = s.strokes - (1 if s.bucket_made else 0)
        rel = eff - PAR_PER_HOLE
        if s.player_id not in per_player:
            per_player[s.player_id] = {
                "effective": 0,
                "relative": 0,
            }
        per_player[s.player_id]["effective"] += eff
        per_player[s.player_id]["relative"] += rel
        
    entries = []
    for pid, agg in per_player.items():
        p = players.get(pid)
        entries.append(
            {
                "player_id": pid,
                "player_name": p.name if p else "Unknown",
                "total_effective_strokes": agg["effective"],
                "total_relative_to_par": agg["relative"],
                "career_wins": p.career_wins if p else 0,
            }
        )
    
    entries.sort(key=lambda e: (e["total_relative_to_par"], e["total_effective_strokes"]))
    
    leaderboard = []
    for idx, e in enumerate(entries):
        leaderboard.append(
            schemas.LeaderboardEntry(
                player_id=e["player_id"],
                player_name=e["player_name"],
                total_effective_strokes=e["total_effective_strokes"],
                total_relative_to_par=e["total_relative_to_par"],
                rank=idx + 1,
                career_wins=e["career_wins"],
            )
        )
    return leaderboard

def finalize_round(db: Session, round_id: int) -> Optional[schemas.RoundResult]:
    leaderboard = compute_leaderboard(db, round_id)
    if not leaderboard:
        return None
    
    winner_entry = leaderboard[0]
    round_obj = get_round(db, round_id)
    winner = get_player(db, winner_entry.player_id)
    
    if round_obj is None or winner is None:
        return None
    
    winner.career_wins += 1
    db_result = models.RoundResult(round_id=round_id, winner_player_id=winner.id)
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    db.refresh(winner)
    
    return schemas.RoundResult(
        round_id=round_id,
        winner_player_id=winner.id,
        winner_name=winner.name,
        timestamp=db_result.timestamp,
    )
    
def get_career_stats(db: Session, player_id: int) -> Optional[schemas.CareerStats]:
    player = get_player(db, player_id)
    if player is None:
        return None
    
    rounds = (
        db.query(models.Round)
        .join(models.ScoreEntry, models.ScoreEntry.round_id == models.Round.id)
        .filter(models.ScoreEntry.player_id == player_id)
        .distinct()
        .all()
    )
    
    total_rounds = len(rounds)
    wins = player.career_wins
    
    from collections import defaultdict
    
    round_relatives = []
    for r in rounds:
        scores = (
            db.query(models.ScoreEntry)
            .filter(
                models.ScoreEntry.round_id == r.id,
                models.ScoreEntry.player_id == player_id,
            )
            .all()
        )
        total_eff = 0
        total_rel = 0
        for s in scores:
            eff = s.strokes - (1 if s.bucket_made else 0)
            rel = eff - PAR_PER_HOLE
            total_eff += eff
            total_rel += rel
        round_relatives.append(total_rel)
        
    best_rel = min(round_relatives) if round_relatives else None
    avg_rel = (sum(round_relatives) / len(round_relatives) if round_relatives else None)
    
    win_pct = (wins / total_rounds * 100) if total_rounds > 0 else 0.0
    
    return schemas.CareerStats(
        player_id=player.id,
        player_name=player.name,
        career_wins=wins,
        total_rounds=total_rounds,
        win_percentage=win_pct,
        best_total_relative_to_par=best_rel,
        average_total_relative_to_par=avg_rel,
    )