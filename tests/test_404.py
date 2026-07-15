import pytest
from flask import Flask
from flask.testing import FlaskClient
from app import app

@pytest.fixture
def client() -> FlaskClient:
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_404_page(client: FlaskClient) -> None:
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b"404 - Page Not Found" in response.data
