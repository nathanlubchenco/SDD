import pytest
from fastapi.testclient import TestClient
from main import app, create_db_and_tables, engine
from sqlmodel import SQLModel, Session
import os

@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown_db():
    # Use a separate test database
    test_db = "sqlite:///./test_data.db"
    app.dependency_overrides = {}
    # Recreate tables
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)
    # Remove test db file if exists
    if os.path.exists("./data.db"):
        os.remove("./data.db")

client = TestClient(app)

def test_add_and_get_item():
    # Add data
    response = client.post("/items/", json={"name": "Test Item", "description": "A test item."})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert data["description"] == "A test item."
    item_id = data["id"]

    # Get data
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data2 = response.json()
    assert data2["id"] == item_id
    assert data2["name"] == "Test Item"
    assert data2["description"] == "A test item."

def test_update_item():
    # Add data
    response = client.post("/items/", json={"name": "Old Name", "description": "Old desc"})
    assert response.status_code == 201
    item_id = response.json()["id"]

    # Update data
    response = client.put(f"/items/{item_id}", json={"name": "New Name", "description": "New desc"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New desc"

    # Get updated data
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data2 = response.json()
    assert data2["name"] == "New Name"
    assert data2["description"] == "New desc"

def test_delete_item():
    # Add data
    response = client.post("/items/", json={"name": "To Delete", "description": "Delete me"})
    assert response.status_code == 201
    item_id = response.json()["id"]

    # Delete data
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 204

    # Try to get deleted data
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 404

def test_list_items():
    # Add multiple items
    for i in range(3):
        client.post("/items/", json={"name": f"Item {i}", "description": f"Desc {i}"})
    response = client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    names = [item["name"] for item in data]
    assert "Item 0" in names
    assert "Item 1" in names
    assert "Item 2" in names
