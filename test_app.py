import subprocess
import os


def test_app_fails_without_secret_key():
    # Remove the secret key from the environment if it exists
    env = os.environ.copy()
    env.pop("FLASK_SECRET_KEY", None)

    # Run app.py as a subprocess
    result = subprocess.run(
        ["python", "app.py"], env=env, capture_output=True, text=True
    )

    # It should fail with a ValueError
    assert result.returncode != 0
    assert "ValueError: No FLASK_SECRET_KEY set for Flask app" in result.stderr


def test_app_starts_with_secret_key():
    # Set the secret key in the environment
    env = os.environ.copy()
    env["FLASK_SECRET_KEY"] = "test_key"

    # Run app.py and quickly kill it to make sure it doesn't crash on import
    # The server starts in app.run(debug=True)
    # We can pass a script that imports app instead of running it
    script = "import app; print('Success')"
    result = subprocess.run(
        ["python", "-c", script], env=env, capture_output=True, text=True
    )

    assert result.returncode == 0
    assert "Success" in result.stdout
