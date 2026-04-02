#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/demo-common.sh
source "$SCRIPT_DIR/demo-common.sh"

require_demo_prereqs

if [ "$#" -gt 0 ]; then
  compose_cmd logs -f --tail=200 "$@"
else
  compose_cmd logs -f --tail=200 orchestrator trainer-1 trainer-2 evaluator-1 anvil postgres
fi
