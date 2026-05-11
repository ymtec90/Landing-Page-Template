import pytest
import sqlite3
import tempfile
import os
from werkzeug.security import generate_password_hash
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        with app.app_context():
            yield client

@pytest.fixture
def test_db(monkeypatch):
    db_fd, db_path = tempfile.mkstemp()

    # Initialize the temp db
    temp_conn = sqlite3.connect(db_path)
    temp_conn.execute(
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        """
    )
    hashed_password = generate_password_hash("testpassword")
    temp_conn.execute(
        "INSERT INTO admins (username, password) VALUES (?, ?)",
        ("admin", hashed_password)
    )
    temp_conn.commit()
    temp_conn.close()

    def mock_get_db_connection():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr("app.get_db_connection", mock_get_db_connection)

    yield

    os.close(db_fd)
    os.unlink(db_path)

def test_login_successful(client, test_db):
    response = client.post("/login", data={"username": "admin", "password": "testpassword"})
    assert response.status_code == 302
    assert response.location == "/interessados"

def test_login_failed_wrong_password(client, test_db):
    response = client.post("/login", data={"username": "admin", "password": "wrongpassword"})
    assert response.status_code == 200
    assert b"Credenciais incorretas." in response.data

def test_login_failed_wrong_username(client, test_db):
    response = client.post("/login", data={"username": "notadmin", "password": "testpassword"})
    assert response.status_code == 200
    assert b"Credenciais incorretas." in response.data

def test_login_get(client, test_db):
    response = client.get("/login")
    assert response.status_code == 200
    # Assuming there's a login form in the HTML
    assert b"<form" in response.data.lower()
