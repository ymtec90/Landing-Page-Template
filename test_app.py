import pytest
from app import app
from flask import session

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret_key"
    with app.test_client() as client:
        yield client

def test_logout(client):
    with client.session_transaction() as sess:
        sess["admin_logged_in"] = True

    response = client.get("/logout")

    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    with client.session_transaction() as sess:
        assert "admin_logged_in" not in sess
