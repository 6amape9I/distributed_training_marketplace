#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/demo-common.sh
source "$SCRIPT_DIR/demo-common.sh"

require_demo_prereqs
compose_cmd down --remove-orphans
log "demo stack stopped"
