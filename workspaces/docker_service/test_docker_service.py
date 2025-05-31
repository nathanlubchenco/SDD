import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'Hello': 'World'}

def test_create_item():
    response = client.post('/items/', json={'item_id': 1, 'name': 'Test Item', 'price': 10.0})
    assert response.status_code == 200
    assert response.json() == {'item': {'name': 'Test Item', 'price': 10.0, 'description': None, 'tax': None}}

def test_read_item():
    client.post('/items/', json={'item_id': 2, 'name': 'Another Item', 'price': 20.0})
    response = client.get('/items/2')
    assert response.status_code == 200
    assert response.json() == {'item': {'name': 'Another Item', 'price': 20.0, 'description': None, 'tax': None}}

def test_health_check():
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'healthy'}