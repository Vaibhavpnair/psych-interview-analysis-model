"""
Tests for the FastAPI backend API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthCheck:
    """Test system health endpoints."""

    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "docs" in response.json()


class TestSessionsAPI:
    """Test session endpoints."""

    def test_list_sessions(self):
        response = client.get("/api/sessions/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestPatientsAPI:
    """Test patient endpoints."""

    def test_list_patients(self):
        response = client.get("/api/patients/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
