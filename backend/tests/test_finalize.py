def test_finalize_round(client):
    p = client.post("/players", json={"name": "Winner"}).json()
    r = client.post("/rounds", json={"date": "2026-06-24", "round_number": 1}).json()
    
    client.post(f"/rounds/{r['id']}/scores", json={"player_id": p["id"], "hole_number": 1, "strokes": 2, "bucket_made": True})
    
    res = client.post(f"/rounds/{r['id']}/finalize")
    assert res.status_code == 200
    assert res.json()["winner_player_id"] == p["id"]
    
    stats = client.get(f"/players/{p['id']}/career").json()
    assert stats["career_wins"] == 1