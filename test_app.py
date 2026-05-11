import subprocess
import os
import time
import requests

def run_app_with_debug(env_value):
    env = os.environ.copy()
    if env_value is not None:
        env["FLASK_DEBUG"] = env_value
    elif "FLASK_DEBUG" in env:
        del env["FLASK_DEBUG"]

    process = subprocess.Popen(
        ["python", "app.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Wait for a brief moment for the app to start and print to stderr
    time.sleep(1)

    # Terminate the process
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()

    stdout, stderr = process.communicate()
    return stdout, stderr

def test_app_debug_off_by_default():
    stdout, stderr = run_app_with_debug(None)
    output = stdout + stderr
    assert "Debug mode: off" in output
    assert "Debug mode: on" not in output

def test_app_debug_enabled_by_env():
    stdout, stderr = run_app_with_debug("True")
    output = stdout + stderr
    assert "Debug mode: on" in output
    assert "Debug mode: off" not in output
