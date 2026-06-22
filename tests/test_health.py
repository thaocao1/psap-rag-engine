import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


def test_liveness_returns_alive():
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["alive"] is True


def test_readiness_returns_ready():
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["ready"] is True
