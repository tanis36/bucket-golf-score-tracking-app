def test_career_stats(client):
    p = client.post("/players", json={"name": "CareerGuy"}).json()
    r = client.post("/rounds", json={"date": "2026-06-24", "round_number": 1}).json()
    
    client.post(f"/rounds/{r['id']}/scores", json={"player_id": p["id"], "hole_number": 1, "strokes": 3, "bucket_made": True})
    
    client.post(f"/rounds/{r['id']}/finalize")
    
    stats = client.get(f"/players/{p['id']}/career").json()
    
    assert stats["career_wins"] == 1
    assert stats["total_rounds"] == 1
    assert stats["win_percentage"] == 100.0