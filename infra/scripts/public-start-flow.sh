#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/public-common.sh
source "$SCRIPT_DIR/public-common.sh"

require_public_prereqs
load_state

[ -n "${JOB_ID:-}" ] || die "JOB_ID is missing from public state"
[ -z "${ROUND_ID:-}" ] || die "ROUND_ID is already set to $ROUND_ID. Clear tmp/public-state for a fresh run."

wait_for_http_ok "$ORCHESTRATOR_BASE_URL/health"

log "starting protocol run for public job $JOB_ID"
protocol_response=$(curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/internal/protocol-runs/start-for-job/$JOB_ID")
ROUND_ID=$(printf '%s' "$protocol_response" | json_get round_id)
[ -n "$ROUND_ID" ] || die "protocol run response did not contain round_id"
write_state

log "waiting for trainer tasks to complete"
start_ts=$(date +%s)
while true; do
  tasks_json=$(curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/training-tasks")
  task_summary=$(printf '%s' "$tasks_json" | "$PYTHON_BIN" -c 'import json, sys; tasks = json.load(sys.stdin); statuses = [task["status"] for task in tasks]; print("missing" if not statuses else "completed" if all(status == "completed" for status in statuses) else "failed" if any(status == "failed" for status in statuses) else "running")')
  case "$task_summary" in
    completed) break ;;
    failed) die "at least one trainer task failed" ;;
    missing) die "no trainer tasks were created for job $JOB_ID" ;;
  esac
  if [ $(( $(date +%s) - start_ts )) -ge "$PUBLIC_TIMEOUT_SECONDS" ]; then
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
  task_summary=$(printf '%s' "$tasks_json" | "$PYTHON_BIN" -c 'import json, sys; tasks = json.load(sys.stdin); statuses = [task["status"] for task in tasks]; print("missing" if not statuses else "completed" if all(status == "completed" for status in statuses) else "failed" if any(status == "failed" for status in statuses) else "running")')
  case "$task_summary" in
    completed) break ;;
    failed) die "the evaluator task failed" ;;
    missing) die "no evaluation task was created for job $JOB_ID" ;;
  esac
  if [ $(( $(date +%s) - start_ts )) -ge "$PUBLIC_TIMEOUT_SECONDS" ]; then
    die "timed out waiting for evaluation task to complete"
  fi
  sleep 2
done

log "reconciling round $ROUND_ID into final off-chain job lifecycle state"
curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/internal/rounds/$ROUND_ID/reconcile" >/dev/null

OFFCHAIN_FINAL_STATUS=$(curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID" | json_get offchain_status)
case "$OFFCHAIN_FINAL_STATUS" in
  ready_for_attestation|evaluation_failed)
    ;;
  *)
    die "unexpected final off-chain job state: $OFFCHAIN_FINAL_STATUS"
    ;;
esac

write_state
log "public flow completed with final off-chain job state: $OFFCHAIN_FINAL_STATUS"
if [ "$OFFCHAIN_FINAL_STATUS" = "ready_for_attestation" ]; then
  log "next step: make public-submit-attestation"
else
  log "success-path on-chain attestation/finalization is skipped because the run ended in evaluation_failed"
fi
