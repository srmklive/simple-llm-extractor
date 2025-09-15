
import os
os.environ["LLM_MODE"] = "mock"

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_empty_input():
    r = client.post("/analyze", json={})
    assert r.status_code == 400

def test_analyze_and_search():
    txt = "OpenAI released a new AI model. The data shows improvements in accuracy."
    r = client.post("/analyze", json={"text": txt})
    assert r.status_code == 200
    payload = r.json()
    assert "results" in payload and len(payload["results"]) == 1

    # Search by a topic expected by the mock ("AI")
    r2 = client.get("/search", params={"topic":"AI"})
    assert r2.status_code == 200
    body = r2.json()
    assert len(body["results"]) >= 1
