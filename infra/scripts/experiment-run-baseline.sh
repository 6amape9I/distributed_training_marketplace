#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
cd "$ROOT_DIR"

PYTHON_BIN=${PYTHON_BIN:-.venv/bin/python}
[ -x "$PYTHON_BIN" ] || { echo "missing python executable: $PYTHON_BIN" >&2; exit 1; }

PYTHONPATH=. "$PYTHON_BIN" -m shared.python.experiments.baseline
