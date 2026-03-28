#!/usr/bin/env python3
"""Simulated Plasma board hardware environment.

This script loads an application module (e.g. chase_web.py) into a
host-side Python process where all hardware-specific imports are
satisfied by stub modules.  It is designed to be launched as a
subprocess by the HIL test suite.

Board / entry-point selection is controlled by environment variables:

  HIL_BOARD         Board name, used to locate the examples folder
                    (default: plasma_2350_w)
  HIL_EXAMPLES_DIR  Path to the examples directory, relative to the
                    repository root.  Derived from HIL_BOARD when not set.
  HIL_ENTRY         Python module name to import and run
                    (default: chase_web)
  WEB_TEST_PORT     TCP port the simulated web server listens on.
                    Overrides the hardcoded port 80 in the application.
                    (default: 8080)
"""

import os
import sys
import time as _time

# ── Configuration ─────────────────────────────────────────────────────────────

_BOARD = os.environ.get("HIL_BOARD", "plasma_2350_w")
_ENTRY = os.environ.get("HIL_ENTRY", "chase_web")

_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Derive examples directory: plasma_2350_w  → examples/plasma2350w
_default_examples = os.path.join(
    _repo_root, "examples", _BOARD.replace("_", "")
)
_examples_dir = os.environ.get("HIL_EXAMPLES_DIR") or _default_examples

os.environ.setdefault("WEB_TEST_PORT", "8080")

# Flush stdout immediately so the parent process can read progress lines
# without waiting for the OS pipe buffer to fill.
sys.stdout.reconfigure(line_buffering=True)

# ── Inject hardware stubs before any application import ──────────────────────

_stubs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stubs")
sys.path.insert(0, _stubs_dir)
sys.path.insert(1, _examples_dir)

# ── Patch the standard `time` module with MicroPython-only helpers ───────────
# ticks_ms / ticks_add / ticks_diff do not exist in CPython's time module.

if not hasattr(_time, "ticks_ms"):
    _MASK = 0x3FFFFFFF

    def _ticks_ms():
        return int(_time.time() * 1000) & _MASK

    def _ticks_add(t, ms):
        return (t + ms) & _MASK

    def _ticks_diff(a, b):
        return ((a - b + 0x1FFFFFFF) & _MASK) - 0x1FFFFFFF

    _time.ticks_ms = _ticks_ms
    _time.ticks_add = _ticks_add
    _time.ticks_diff = _ticks_diff

# Make time.sleep() instant for the simulation environment.
# wifi_connect() calls time.sleep() three times (2 × 1 s + 1 × 2 s) while
# waiting for the CYW43 hardware to become ready.  The stub network.WLAN
# always reports a successful connection immediately, so those delays serve
# no purpose here and would add ~4 s to every test run.
_time.sleep = lambda _s: None

# ── Import and run the target application module ──────────────────────────────

print(f"[SIM] Board  : {_BOARD}", flush=True)
print(f"[SIM] Entry  : {_ENTRY}", flush=True)
print(f"[SIM] Port   : {os.environ['WEB_TEST_PORT']}", flush=True)

import importlib
importlib.import_module(_ENTRY)
