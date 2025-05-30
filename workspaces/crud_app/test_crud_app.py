import pytest
from fastapi.testclient import TestClient
from main import app, data_store

client = TestClient(app)


def test_add_data():
    response = client.post("/data/", json={"id": 1, "value": "test value"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "value": "test value"}
    assert data_store[1] == "test value"


def test_get_data():
    data_store[1] = "test value"
    response = client.get("/data/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "value": "test value"}


def test_update_data():
    data_store[1] = "test value"
    response = client.put("/data/1", json={"id": 1, "value": "updated value"})
    assert response.status_code == 200
    assert response.json() == {"id": 1, "value": "updated value"}
    assert data_store[1] == "updated value"


def test_delete_data():
    data_store[1] = "test value"
    response = client.delete("/data/1")
    assert response.status_code == 200
    assert response.json() == {"id": 1, "value": "test value"}
    assert 1 not in data_store


def test_get_data_not_found():
    response = client.get("/data/999")
    assert response.status_code == 404


def test_update_data_not_found():
    response = client.put("/data/999", json={"id": 999, "value": "value"})
    assert response.status_code == 404


def test_delete_data_not_found():
    response = client.delete("/data/999")
    assert response.status_code == 404
