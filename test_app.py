import pytest
import sqlite3
import os
import tempfile
import app as my_app
from app import app
from werkzeug.security import check_password_hash

@pytest.fixture
def temp_db():
    db_fd, db_path = tempfile.mkstemp()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    conn.execute(
        """
                 CREATE TABLE IF NOT EXISTS interessados (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 nome TEXT NOT NULL,
                 email TEXT NOT NULL,
                 motivo TEXT
                 );
        """
    )

    conn.execute(
        """
                 CREATE TABLE IF NOT EXISTS admins (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT NOT NULL UNIQUE,
                 password TEXT NOT NULL
                 );
        """
    )
    conn.commit()
    conn.close()

    yield db_path

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(monkeypatch, temp_db):
    app.config['TESTING'] = True

    def get_mock_db_connection():
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        return conn

    monkeypatch.setattr(my_app, "get_db_connection", get_mock_db_connection)

    with app.test_client() as client:
        yield client

def test_setup_admin_get_no_admin(client):
    response = client.get("/setup")
    assert response.status_code == 200
    assert b"Setup" in response.data or b"setup" in response.data or b"<form" in response.data # Check some page content since we mocked everything

def test_setup_admin_post_create_admin(client, temp_db):
    response = client.post("/setup", data={
        "username": "admin",
        "password": "password123"
    })

    assert response.status_code == 302
    assert "/interessados" in response.headers["Location"]

    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    admin = conn.execute("SELECT * FROM admins").fetchone()
    conn.close()

    assert admin is not None
    assert admin["username"] == "admin"
    assert check_password_hash(admin["password"], "password123")

    with client.session_transaction() as session:
        assert session.get("admin_logged_in") is True

def test_setup_admin_already_exists(client, temp_db):
    conn = sqlite3.connect(temp_db)
    conn.execute("INSERT INTO admins (username, password) VALUES ('existing_admin', 'hash')")
    conn.commit()
    conn.close()

    response = client.get("/setup")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    response_post = client.post("/setup", data={
        "username": "new_admin",
        "password": "password"
    })
    assert response_post.status_code == 302
    assert "/login" in response_post.headers["Location"]
