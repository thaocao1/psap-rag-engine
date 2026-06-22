import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_query_returns_response():
    response = client.post(
        "/api/v1/query",
        json={"question": "What is the MSAG validation procedure?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "latency_ms" in data


def test_query_rejects_empty_question():
    response = client.post("/api/v1/query", json={"question": ""})
    assert response.status_code == 422


def test_query_rejects_short_question():
    response = client.post("/api/v1/query", json={"question": "hi"})
    assert response.status_code == 422


def test_query_respects_top_k():
    response = client.post(
        "/api/v1/query",
        json={"question": "What is ESN routing?", "top_k": 5},
    )
    assert response.status_code == 200


def test_query_rejects_invalid_top_k():
    response = client.post(
        "/api/v1/query",
        json={"question": "What is ESN routing?", "top_k": 99},
    )
    assert response.status_code == 422
