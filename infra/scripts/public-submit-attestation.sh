#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/public-common.sh
source "$SCRIPT_DIR/public-common.sh"

require_public_prereqs
load_state
require_env ATTESTOR_PRIVATE_KEY
require_env PUBLIC_RPC_URL

[ -n "${JOB_ID:-}" ] || die "missing JOB_ID in public state"
[ -n "${ROUND_ID:-}" ] || die "missing ROUND_ID in public state"
[ "${OFFCHAIN_FINAL_STATUS:-}" = "ready_for_attestation" ] || die "public attestation requires off-chain status ready_for_attestation"

wait_for_http_ok "$ORCHESTRATOR_BASE_URL/health"
validate_rpc_chain

job_json_path="$STATE_DIR/job-${JOB_ID}.json"
round_json_path="$STATE_DIR/round-${ROUND_ID}.json"
evaluation_json_path="$STATE_DIR/evaluation-${JOB_ID}.json"
ATT_PAYLOAD_PATH="$STATE_DIR/job-${JOB_ID}-attestation.json"

capture_json "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID" "$job_json_path"
capture_json "$ORCHESTRATOR_BASE_URL/rounds/$ROUND_ID" "$round_json_path"
capture_json "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/evaluation-tasks" "$STATE_DIR/evaluation-tasks-${JOB_ID}.json"
"$PYTHON_BIN" - "$STATE_DIR/evaluation-tasks-${JOB_ID}.json" "$evaluation_json_path" <<'PY'
import json
import sys
from pathlib import Path

tasks = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
completed = [task for task in tasks if task["status"] == "completed"]
if len(completed) != 1:
    raise SystemExit(f"expected exactly one completed evaluation task, got {len(completed)}")
Path(sys.argv[2]).write_text(json.dumps(completed[0], indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

"$PYTHON_BIN" -m shared.python.public_demo attestation \
  --network "$PUBLIC_NETWORK" \
  --chain-id "$PUBLIC_CHAIN_ID" \
  --contract-address "$CONTRACT_ADDRESS" \
  --job-json "$job_json_path" \
  --round-json "$round_json_path" \
  --evaluation-json "$evaluation_json_path" >"$ATT_PAYLOAD_PATH"

ATTESTATION_HASH=$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["hash"])' "$ATT_PAYLOAD_PATH")
onchain_job=$("$PYTHON_BIN" -m shared.python.public_demo onchain-job \
  --rpc-url "$PUBLIC_RPC_URL" \
  --contract-address "$CONTRACT_ADDRESS" \
  --job-id "$JOB_ID")
existing_hash=$(printf '%s' "$onchain_job" | json_get attestation_hash)
existing_status=$(printf '%s' "$onchain_job" | json_get status)

if [ -n "$existing_hash" ]; then
  [ "$existing_hash" = "$ATTESTATION_HASH" ] || die "on-chain attestation hash mismatch: expected $ATTESTATION_HASH, got $existing_hash"
  case "$existing_status" in
    attested|finalized)
      log "attestation already present on-chain"
      write_state
      log "next step: make public-finalize-job"
      exit 0
      ;;
  esac
fi

log "submitting attestation for public job $JOB_ID"
ATTESTATION_TX_HASH=$(send_tx_async "$CONTRACT_ADDRESS" \
  "submitAttestation(uint256,bytes32)" \
  "$JOB_ID" \
  "$ATTESTATION_HASH" \
  --rpc-url "$PUBLIC_RPC_URL" \
  --private-key "$ATTESTOR_PRIVATE_KEY")
wait_for_receipt_json "$ATTESTATION_TX_HASH" >/dev/null

curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/jobs/sync" >/dev/null
onchain_job=$("$PYTHON_BIN" -m shared.python.public_demo onchain-job \
  --rpc-url "$PUBLIC_RPC_URL" \
  --contract-address "$CONTRACT_ADDRESS" \
  --job-id "$JOB_ID")
attested_hash=$(printf '%s' "$onchain_job" | json_get attestation_hash)
attested_status=$(printf '%s' "$onchain_job" | json_get status)
[ "$attested_hash" = "$ATTESTATION_HASH" ] || die "attestation hash was not persisted on-chain"
[ "$attested_status" = "attested" ] || die "expected on-chain job status attested, got $attested_status"

write_state
log "attestation submitted with hash $ATTESTATION_HASH"
log "next step: make public-finalize-job"
