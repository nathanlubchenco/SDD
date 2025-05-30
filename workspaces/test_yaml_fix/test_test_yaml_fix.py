import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_add_numbers():
    response = client.post("/add", json={"a": 5, "b": 3})
    assert response.status_code == 200
    assert response.json() == {"result": 8}

def test_add_numbers_response_time():
    response = client.post("/add", json={"a": 5, "b": 3})
    assert response.elapsed.total_seconds() * 1000 < 100

def test_divide_numbers():
    response = client.post("/divide", json={"a": 10, "b": 2})
    assert response.status_code == 200
    assert response.json() == {"result": 5.0}

def test_divide_by_zero():
    response = client.post("/divide", json={"a": 10, "b": 0})
    assert response.status_code == 400
    assert response.json() == {"detail": "Division by zero is not allowed"}
