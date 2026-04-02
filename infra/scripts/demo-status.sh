#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/demo-common.sh
source "$SCRIPT_DIR/demo-common.sh"

require_demo_prereqs

log "orchestrator /health"
curl -fsS "$ORCHESTRATOR_BASE_URL/health" | pretty_json

printf '\n'
log "orchestrator /status"
curl -fsS "$ORCHESTRATOR_BASE_URL/status" | pretty_json

printf '\n'
log "registered nodes"
curl -fsS "$ORCHESTRATOR_BASE_URL/nodes" | pretty_json

printf '\n'
log "jobs"
curl -fsS "$ORCHESTRATOR_BASE_URL/jobs" | pretty_json

if [ -f "$STATE_FILE" ]; then
  load_state
  if [ -n "${JOB_ID:-}" ]; then
    printf '\n'
    log "job $JOB_ID details"
    curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID" | pretty_json

    printf '\n'
    log "job $JOB_ID rounds"
    curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/rounds" | pretty_json

    printf '\n'
    log "job $JOB_ID training tasks"
    curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/training-tasks" | pretty_json

    printf '\n'
    log "job $JOB_ID evaluation tasks"
    curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/evaluation-tasks" | pretty_json
  fi

  if [ -n "${ROUND_ID:-}" ]; then
    printf '\n'
    log "round $ROUND_ID details"
    curl -fsS "$ORCHESTRATOR_BASE_URL/rounds/$ROUND_ID" | pretty_json
  fi
fi

printf '\n'
log "trainer-1 /status"
curl -fsS "http://127.0.0.1:8010/status" | pretty_json

printf '\n'
log "trainer-2 /status"
curl -fsS "http://127.0.0.1:8011/status" | pretty_json

printf '\n'
log "evaluator-1 /status"
curl -fsS "http://127.0.0.1:8020/status" | pretty_json
