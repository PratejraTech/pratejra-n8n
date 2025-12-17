#!/usr/bin/env bash
# Purpose: Run pytest in this repo without relying on externally auto-loaded pytest plugins
# Created/Updated: 2025-12-17 00:00
# Agent: GPT-5.2
#
# Why:
# Some environments have pytest plugins installed (e.g., pytest-playwright) without their full deps,
# causing `pytest` to fail before tests start (example: missing `greenlet`).
#
# This runner disables plugin autoload so the repo tests can run deterministically.

set -euo pipefail

export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
python -m pytest -q "$@"


