from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_index_serves_frontend():
    response = client.get("/")
    assert response.status_code == 200
    assert "ROOTCAUSE" in response.text


def test_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert "gemini_configured" in response.json()


def test_create_session_and_set_variables():
    session = client.post("/api/session").json()
    session_id = session["session_id"]

    response = client.post("/api/variables", json={
        "session_id": session_id,
        "variables": {"soil_organic_carbon": 0.4, "rainfall_level": 280},
    })
    assert response.status_code == 200
    assert response.json()["known_variables"]["rainfall_level"] == 280


def test_unknown_session_returns_404():
    response = client.get("/api/variables/not-a-real-session")
    assert response.status_code == 404


def test_reset_clears_variables():
    session_id = client.post("/api/session").json()["session_id"]
    client.post("/api/variables", json={"session_id": session_id, "variables": {"rainfall_level": 500}})
    client.post("/api/reset", json={"session_id": session_id, "message": ""})
    response = client.get(f"/api/variables/{session_id}")
    assert response.json()["known_variables"] == {}
