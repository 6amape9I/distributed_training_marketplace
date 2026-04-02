#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/demo-common.sh
source "$SCRIPT_DIR/demo-common.sh"

require_demo_prereqs

log "starting base services"
compose_cmd up -d --build anvil postgres
wait_for_service_health anvil
wait_for_service_health postgres

log "running orchestrator database migrations"
compose_run_tool db-migrate

log "starting orchestrator and workers"
compose_cmd up -d --build orchestrator trainer-1 trainer-2 evaluator-1
wait_for_service_health orchestrator
wait_for_service_health trainer-1
wait_for_service_health trainer-2
wait_for_service_health evaluator-1

wait_for_http_ok "$ORCHESTRATOR_BASE_URL/health"
wait_for_http_ok "http://127.0.0.1:8010/health"
wait_for_http_ok "http://127.0.0.1:8011/health"
wait_for_http_ok "http://127.0.0.1:8020/health"

log "demo stack is up"
log "next step: make demo-init"
