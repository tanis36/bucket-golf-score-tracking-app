def test_websocket_score_updates(client):
    p = client.post("/players", json={"name": "WS"}).json()
    r = client.post("/rounds", json={"date": "2026-06-24", "round_number": 1}).json()
    
    with client.websocket_connect(f"/ws/rounds/{r['id']}") as ws:
        client.post(f"/rounds/{r['id']}/scores", json={
            "player_id": p["id"],
            "hole_number": 1,
            "strokes": 3,
            "bucket_made": True
        })
        
        message = ws.receive_json()
        assert message["type"] == "score_update"
        assert len(message["leaderboard"]) == 1