import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_add_numbers():
    response = client.post("/add", json={"a": 5, "b": 3})
    assert response.status_code == 200
    assert response.json()["result"] == 8
    assert response.json()["response_time_ms"] < 100

def test_divide_by_zero():
    response = client.post("/divide", json={"a": 5, "b": 0})
    assert response.status_code == 400
    assert "Division by zero is not allowed." in response.json()["detail"]

def test_divide_numbers():
    response = client.post("/divide", json={"a": 10, "b": 2})
    assert response.status_code == 200
    assert response.json()["result"] == 5

def test_invalid_input():
    response = client.post("/add", json={"a": "five", "b": 3})
    assert response.status_code == 422
    assert "Invalid input" in response.json()["detail"]
