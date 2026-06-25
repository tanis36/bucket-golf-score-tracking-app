def test_create_round(client):
    res = client.post("/rounds", json={"date": "2026-06-24", "round_number": 1})
    assert res.status_code == 200
    assert res.json()["round_number"] == 1
    
def test_get_rounds_by_date(client):
    res = client.get("/rounds", params={"date": "2026-06-24"})
    assert res.status_code == 200
    assert len(res.json()) >= 1