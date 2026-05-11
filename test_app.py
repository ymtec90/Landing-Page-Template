import os
import tempfile
import pytest
from werkzeug.security import check_password_hash

# Create temp db path and set env vars *before* importing app
# To ensure tests are isolated, we use conftest or early setup.
# Here we setup environment *before* import, but manage DB lifecycle per fixture.
os.environ['TESTING'] = 'True'
os.environ['DB_PATH'] = '/tmp/test_database.db' # Use a static name to satisfy import, replace in fixture

from app import app, create_table, get_db_connection

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    os.environ['DB_PATH'] = db_path
    app.config['TESTING'] = True

    # Ensure tables are created
    create_table()

    with app.test_client() as client:
        yield client

    # Clean up after test
    try:
        os.close(db_fd)
    except OSError:
        pass
    try:
        os.unlink(db_path)
    except OSError:
        pass

def test_landing_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

def test_submit_form(client):
    response = client.post("/submit", data={
        "nome": "Test User",
        "email": "test@example.com",
        "motivo": "Testing the submission form"
    })
    assert response.status_code == 200
    assert b"Test User" in response.data

    # Verify data is in DB
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM interessados WHERE email = 'test@example.com'").fetchone()
    conn.close()
    assert user is not None
    assert user['nome'] == "Test User"
    assert user['motivo'] == "Testing the submission form"

def test_setup_admin(client):
    # Admin setup should work if no admin exists
    response = client.post("/setup", data={
        "username": "admin",
        "password": "password123"
    })
    # Should redirect to list after setup
    assert response.status_code == 302
    assert response.location.endswith("/interessados")

    # Verify admin in DB
    conn = get_db_connection()
    admin = conn.execute("SELECT * FROM admins WHERE username = 'admin'").fetchone()
    conn.close()
    assert admin is not None
    assert check_password_hash(admin['password'], 'password123')

    # Trying to setup again should redirect to login
    response2 = client.get("/setup")
    assert response2.status_code == 302
    assert response2.location.endswith("/login")

def test_table_migration(client):
    # Setup test table using old name 'usuarios'
    conn = get_db_connection()
    conn.execute("DROP TABLE IF EXISTS interessados;")
    conn.execute("DROP TABLE IF EXISTS usuarios;")
    conn.execute(
        """
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            motivo TEXT
        );
        """
    )
    conn.commit()
    conn.close()

    # Call create_table which should trigger the migration
    create_table()

    # Verify migration occurred
    conn = get_db_connection()
    # Check that 'usuarios' doesn't exist anymore
    old_table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios';").fetchone()
    assert old_table is None

    # Check that 'interessados' exists
    new_table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interessados';").fetchone()
    assert new_table is not None
    conn.close()

def test_setup_admin_get(client):
    # Test GET request to /setup when no admin exists
    response = client.get("/setup")
    assert response.status_code == 200
    assert b"<form" in response.data # Check that a form is returned (setup.html)

def test_login_get(client):
    # Test GET request to /login
    response = client.get("/login")
    assert response.status_code == 200
    assert b"<form" in response.data # Check that a form is returned (login.html)

def test_login_logout(client):
    # Setup first
    client.post("/setup", data={
        "username": "admin",
        "password": "password123"
    })
    # Logout first (setup logs us in)
    client.get("/logout")

    # Correct login
    response = client.post("/login", data={
        "username": "admin",
        "password": "password123"
    })
    assert response.status_code == 302
    assert response.location.endswith("/interessados")

    with client.session_transaction() as sess:
        assert sess.get('admin_logged_in') is True

    # Logout
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.location.endswith("/")

    with client.session_transaction() as sess:
        assert sess.get('admin_logged_in') is None

    # Incorrect login
    response = client.post("/login", data={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 200
    assert b"Credenciais incorretas." in response.data

def test_interessados_access(client):
    # Access without admin setup
    response = client.get("/interessados")
    assert response.status_code == 302
    assert response.location.endswith("/setup")

    # Setup admin
    client.post("/setup", data={
        "username": "admin",
        "password": "password123"
    })

    # Access while logged in
    response = client.get("/interessados")
    assert response.status_code == 200

    # Access after logout
    client.get("/logout")
    response = client.get("/interessados")
    assert response.status_code == 302
    assert response.location.endswith("/login")
