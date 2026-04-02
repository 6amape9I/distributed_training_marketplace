#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/public-common.sh
source "$SCRIPT_DIR/public-common.sh"

require_public_prereqs
load_state

[ -n "${JOB_ID:-}" ] || die "missing JOB_ID in public state"
wait_for_http_ok "$ORCHESTRATOR_BASE_URL/health"

log "syncing public job $JOB_ID into orchestrator"
curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/jobs/sync" >/dev/null

start_ts=$(date +%s)
while true; do
  if curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID" >/dev/null 2>&1; then
    break
  fi
  if [ $(( $(date +%s) - start_ts )) -ge "$PUBLIC_TIMEOUT_SECONDS" ]; then
    die "timed out waiting for orchestrator to expose job $JOB_ID"
  fi
  sleep 2
done

log "waiting for trainer and evaluator nodes to become online"
start_ts=$(date +%s)
while true; do
  nodes_json=$(curl -fsS "$ORCHESTRATOR_BASE_URL/nodes")
  online_count=$(printf '%s' "$nodes_json" | "$PYTHON_BIN" -c 'import json, sys; nodes = json.load(sys.stdin); expected = {"trainer-1", "trainer-2", "evaluator-1"}; online = {node["node_id"] for node in nodes if node["status"] == "online"}; print(1 if expected.issubset(online) else 0)')
  if [ "$online_count" = "1" ]; then
    break
  fi
  if [ $(( $(date +%s) - start_ts )) -ge "$PUBLIC_TIMEOUT_SECONDS" ]; then
    die "timed out waiting for trainer/evaluator nodes to become online"
  fi
  sleep 2
done

log "moving public job $JOB_ID into scheduling"
for _ in 1 2 3 4 5; do
  curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/internal/lifecycle/reconcile" >/dev/null
  job_status=$(curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID" | json_get offchain_status)
  if [ "$job_status" = "scheduling" ]; then
    break
  fi
  sleep 2
done

job_status=$(curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID" | json_get offchain_status)
[ "$job_status" = "scheduling" ] || die "expected job $JOB_ID to reach scheduling, got $job_status"

write_state
log "job $JOB_ID is visible and ready for the protocol flow"
log "next step: make public-start-flow"
