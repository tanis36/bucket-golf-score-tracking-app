def test_create_player(client):
    res = client.post("/players", json={"name": "Tanis"})
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Tanis"
    assert data["career_wins"] == 0
    
def test_list_players(client):
    res = client.get("/players")
    assert res.status_code == 200
    assert isinstance(res.json(), list)