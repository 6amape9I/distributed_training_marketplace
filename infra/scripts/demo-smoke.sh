#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

"$SCRIPT_DIR/demo-clean.sh"
"$SCRIPT_DIR/demo-up.sh"
"$SCRIPT_DIR/demo-init.sh"
"$SCRIPT_DIR/demo-start-flow.sh"
"$SCRIPT_DIR/demo-status.sh"

printf '[demo] smoke run completed; stack is still running for inspection\n'
