def test_submit_score(client):
    p = client.post("/players", json={"name": "Player1"}).json()
    r = client.post("/rounds", json={"date": "2026-06-24", "round_number": 1}).json()
    
    payload = {
        "player_id": p["id"],
        "hole_number": 1,
        "strokes": 3,
        "bucket_made": True
    }
    
    res = client.post(f"/rounds/{r['id']}/scores", json=payload)
    assert res.status_code == 200
    assert res.json()["strokes"] == 3
    assert res.json()["bucket_made"] is True