#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/demo-common.sh
source "$SCRIPT_DIR/demo-common.sh"

require_demo_prereqs
require_host_port_free 8000
require_host_port_free 8010
require_host_port_free 8011
require_host_port_free 8020

log "starting base services"
compose_cmd up -d --build anvil postgres orchestrator
wait_for_service_health anvil
wait_for_service_health postgres
wait_for_service_health orchestrator

log "running orchestrator database migrations"
compose_cmd exec -T orchestrator python -m alembic -c orchestrator/alembic.ini upgrade head

log "starting workers"
compose_cmd up -d --build trainer-1 trainer-2 evaluator-1
wait_for_service_health trainer-1
wait_for_service_health trainer-2
wait_for_service_health evaluator-1

wait_for_http_ok "$ORCHESTRATOR_BASE_URL/health"
wait_for_http_ok "http://127.0.0.1:8010/health"
wait_for_http_ok "http://127.0.0.1:8011/health"
wait_for_http_ok "http://127.0.0.1:8020/health"

log "demo stack is up"
log "next step: make demo-init"
