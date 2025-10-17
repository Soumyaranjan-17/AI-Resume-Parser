import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_supported_formats():
    response = client.get("/supported-formats")
    assert response.status_code == 200
    data = response.json()
    assert "supported_formats" in data
    assert ".pdf" in data["supported_formats"]

def test_parse_resume_invalid_file():
    response = client.post(
        "/parse-resume",
        files={"file": ("test.txt", b"invalid content", "text/plain")}
    )
    assert response.status_code == 400

def test_parse_resume_empty_file():
    response = client.post(
        "/parse-resume", 
        files={"file": ("empty.pdf", b"", "application/pdf")}
    )
    assert response.status_code == 400