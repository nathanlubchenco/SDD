import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_add_numbers():
    response = client.post("/add", json={"number1": 5, "number2": 3})
    assert response.status_code == 200
    assert response.json() == {"result": 8}


def test_divide_numbers():
    response = client.post("/divide", json={"number1": 10, "number2": 2})
    assert response.status_code == 200
    assert response.json() == {"result": 5.0}


def test_divide_by_zero():
    response = client.post("/divide", json={"number1": 10, "number2": 0})
    assert response.status_code == 400
    assert response.json() == {"detail": "Cannot divide by zero"}


def test_invalid_input():
    response = client.post("/add", json={"number1": "five", "number2": 3})
    assert response.status_code == 422
