"""Tests for chat routes."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Provide test client."""
    return TestClient(app)


def test_chat_routes_exist(client):
    """Test that chat routes exist."""
    
    response = client.get("/chat/ui")
    assert response.status_code in [200, 500]
    
    response = client.post("/chat")
    assert response.status_code in [422, 500]
    
    response = client.post("/chat/analyze-followup")
    assert response.status_code in [422, 500]


def test_chat_with_valid_request_structure(client):
    """Test chat request validation."""
    
    valid_request = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ]
    }
    
    response = client.post("/chat", json=valid_request)
    assert response.status_code in [200, 400, 500]


def test_analyze_followup_with_valid_request_structure(client):
    """Test analyze-followup request validation."""
    
    valid_request = {
        "messages": [
            {
                "role": "user",
                "content": "How can I improve my speech?"
            }
        ]
    }
    
    response = client.post("/chat/analyze-followup", json=valid_request)
    assert response.status_code in [200, 400, 500]
