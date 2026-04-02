#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/demo-common.sh
source "$SCRIPT_DIR/demo-common.sh"

require_demo_prereqs
load_state

[ -n "${JOB_ID:-}" ] || die "JOB_ID is missing from demo state"
if [ -n "${ROUND_ID:-}" ]; then
  die "ROUND_ID is already set to $ROUND_ID. Run make demo-clean for a fresh demo."
fi

wait_for_http_ok "$ORCHESTRATOR_BASE_URL/health"

log "starting protocol run for job $JOB_ID"
protocol_response=$(curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/internal/protocol-runs/start-for-job/$JOB_ID")
ROUND_ID=$(printf '%s' "$protocol_response" | json_get round_id)
[ -n "$ROUND_ID" ] || die "protocol run response did not contain round_id"
write_state

log "waiting for trainer tasks to complete"
start_ts=$(date +%s)
while true; do
  tasks_json=$(curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/training-tasks")
  task_summary=$(printf '%s' "$tasks_json" | python3 -c 'import json, sys; tasks = json.load(sys.stdin); statuses = [task["status"] for task in tasks]; print("missing" if not statuses else "completed" if all(status == "completed" for status in statuses) else "failed" if any(status == "failed" for status in statuses) else "running")')
  case "$task_summary" in
    completed) break ;;
    failed) die "at least one trainer task failed" ;;
    missing) die "no trainer tasks were created for job $JOB_ID" ;;
  esac
  if [ $(( $(date +%s) - start_ts )) -ge "$DEMO_TIMEOUT_SECONDS" ]; then
    die "timed out waiting for trainer tasks to complete"
  fi
  sleep 2
done

log "reconciling round $ROUND_ID into aggregation and evaluation"
curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/internal/rounds/$ROUND_ID/reconcile" >/dev/null

log "waiting for evaluator task to complete"
start_ts=$(date +%s)
while true; do
  tasks_json=$(curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/evaluation-tasks")
  task_summary=$(printf '%s' "$tasks_json" | python3 -c 'import json, sys; tasks = json.load(sys.stdin); statuses = [task["status"] for task in tasks]; print("missing" if not statuses else "completed" if all(status == "completed" for status in statuses) else "failed" if any(status == "failed" for status in statuses) else "running")')
  case "$task_summary" in
    completed) break ;;
    failed) die "the evaluator task failed" ;;
    missing) die "no evaluation task was created for job $JOB_ID" ;;
  esac
  if [ $(( $(date +%s) - start_ts )) -ge "$DEMO_TIMEOUT_SECONDS" ]; then
    die "timed out waiting for evaluation task to complete"
  fi
  sleep 2
done

log "reconciling round $ROUND_ID into final job lifecycle state"
curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/internal/rounds/$ROUND_ID/reconcile" >/dev/null

final_status=$(curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID" | json_get offchain_status)
case "$final_status" in
  ready_for_attestation|evaluation_failed)
    ;;
  *)
    die "unexpected final job state: $final_status"
    ;;
esac

log "demo flow completed with final job state: $final_status"
log "inspect current state with: make demo-status"
