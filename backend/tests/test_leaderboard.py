def test_leaderboard_logic(client):
    p1 = client.post("/players", json={"name": "A"}).json()
    p2 = client.post("/players", json={"name": "B"}).json()
    
    r = client.post("/rounds", json={"date": "2026-06-24", "round_number": 1}).json()
    
    client.post(f"/rounds/{r['id']}/scores", json={"player_id": p1["id"], "hole_number": 1, "strokes": 2, "bucket_made": True})
    
    client.post(f"/rounds/{r['id']}/scores", json={"player_id": p2["id"], "hole_number": 1, "strokes": 4, "bucket_made": False})
    
    lb = client.get(f"/leaderboard/round/{r['id']}").json()
    
    assert lb[0]["player_name"] == "A"
    assert lb[0]["rank"] == 1