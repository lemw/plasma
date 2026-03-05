#!/usr/bin/env bash
# ci/hil_sim.sh — HIL simulation helpers for the Plasma boards.
#
# Usage (source this file, then call the functions):
#   source ci/hil_sim.sh
#   hil_prepare
#   hil_run_tests [<board>]        # default board: plasma_2350_w
#
# Environment variables
#   HIL_BOARD         Override the target board name.
#   WEB_TEST_PORT     TCP port used by the simulated web server (default: 8080).

export TERM=${TERM:="xterm-256color"}

function log_success { echo -e "$(tput setaf 2)$1$(tput sgr0)"; }
function log_inform  { echo -e "$(tput setaf 6)$1$(tput sgr0)"; }
function log_warning { echo -e "$(tput setaf 1)$1$(tput sgr0)"; }

# Install Python test dependencies required by the HIL simulation suite.
function hil_prepare {
    log_inform "Installing HIL test dependencies…"
    pip install pytest requests
}

# Run the HIL simulation tests.
#   $1  Board name (optional, defaults to plasma_2350_w or $HIL_BOARD).
function hil_run_tests {
    local board="${1:-${HIL_BOARD:-plasma_2350_w}}"
    local port="${WEB_TEST_PORT:-8080}"

    log_inform "Running simulated HIL tests for board: $board  (port $port)"

    HIL_BOARD="$board" \
    WEB_TEST_PORT="$port" \
    python -m pytest tests/sim/ -v
}

if [ -z "${CI_USE_ENV+x}" ]; then
    SCRIPT_PATH="$(dirname "$0")"
    CI_PROJECT_ROOT=$(realpath "$SCRIPT_PATH/..")
fi
