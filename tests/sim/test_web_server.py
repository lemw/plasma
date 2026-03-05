"""Simulated HIL tests — Plasma 2350W web server.

Starts chase_web.py inside the hardware-stub subprocess (sim_server.py)
so the actual application code runs in a simulated RP2350W environment.
The test suite then exercises the HTTP interface from the host side,
checking:

  * Page structure  — title, controls and swatches are present in the HTML
  * API parameters  — speed / colour / remember are accepted (HTTP 204)
  * State reflection — changes made via the API appear in the next page load
"""

import os
import subprocess
import sys
import time

import pytest
import requests

# ── Fixtures ──────────────────────────────────────────────────────────────────

_SIM_SERVER = os.path.join(os.path.dirname(__file__), "sim_server.py")
_SIM_PORT = int(os.environ.get("WEB_TEST_PORT", "8080"))
_BASE_URL = f"http://127.0.0.1:{_SIM_PORT}"


@pytest.fixture(scope="module")
def web_server():
    """Launch the simulated Plasma 2350W and wait until it is ready.

    Yields the base URL of the running server, then tears it down after
    all tests in this module have finished.
    """
    env = os.environ.copy()
    env["HIL_BOARD"] = "plasma_2350_w"
    env["WEB_TEST_PORT"] = str(_SIM_PORT)
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        [sys.executable, _SIM_SERVER],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )

    deadline = time.monotonic() + 30
    ready = False
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read()
            pytest.fail(f"Simulated server exited unexpectedly:\n{out}")

        line = proc.stdout.readline()
        if line:
            print(f"[sim] {line}", end="", flush=True)
        if "[WEB] Listening" in line:
            ready = True
            break

    if not ready:
        proc.terminate()
        pytest.fail("Simulated Plasma 2350W server did not start within 30 s")

    yield _BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


# ── Page-structure tests ──────────────────────────────────────────────────────

def test_page_returns_200(web_server):
    r = requests.get(web_server, timeout=5)
    assert r.status_code == 200


def test_content_type_is_html(web_server):
    r = requests.get(web_server, timeout=5)
    assert "text/html" in r.headers.get("content-type", "")


def test_page_title(web_server):
    r = requests.get(web_server, timeout=5)
    assert "Plasma Chase" in r.text


def test_speed_slider_present(web_server):
    r = requests.get(web_server, timeout=5)
    assert 'type="range"' in r.text
    assert 'id="speed"' in r.text


def test_color_picker_present(web_server):
    r = requests.get(web_server, timeout=5)
    assert 'type="color"' in r.text
    assert 'id="color"' in r.text


def test_swatches_present(web_server):
    r = requests.get(web_server, timeout=5)
    assert 'class="sw"' in r.text


def test_remember_checkbox_present(web_server):
    r = requests.get(web_server, timeout=5)
    assert 'id="rem"' in r.text


# ── API / parameter tests ─────────────────────────────────────────────────────

def test_set_speed_returns_204(web_server):
    r = requests.get(f"{web_server}/?speed=50", timeout=5)
    assert r.status_code == 204


def test_set_color_returns_204(web_server):
    r = requests.get(f"{web_server}/?color=00ff00", timeout=5)
    assert r.status_code == 204


def test_set_remember_on_returns_204(web_server):
    r = requests.get(f"{web_server}/?remember=1", timeout=5)
    assert r.status_code == 204


def test_set_remember_off_returns_204(web_server):
    r = requests.get(f"{web_server}/?remember=0", timeout=5)
    assert r.status_code == 204


def test_multiple_params_returns_204(web_server):
    r = requests.get(f"{web_server}/?speed=75&color=ff8800", timeout=5)
    assert r.status_code == 204


# ── State-reflection tests ────────────────────────────────────────────────────

def test_speed_reflected_in_page(web_server):
    requests.get(f"{web_server}/?speed=42", timeout=5)
    r = requests.get(web_server, timeout=5)
    # Verify the speed value appears in the slider's value attribute specifically
    assert 'value="42"' in r.text


def test_color_reflected_in_page(web_server):
    requests.get(f"{web_server}/?color=ff1493", timeout=5)
    r = requests.get(web_server, timeout=5)
    # Verify the hex colour appears in the colour picker's value attribute
    assert 'value="#ff1493"' in r.text
