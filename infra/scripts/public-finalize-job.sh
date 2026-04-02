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
[ -n "${ATTESTATION_HASH:-}" ] || die "missing ATTESTATION_HASH in public state"

validate_rpc_chain
wait_for_http_ok "$ORCHESTRATOR_BASE_URL/health"

job_json_path="$STATE_DIR/job-${JOB_ID}.json"
round_json_path="$STATE_DIR/round-${ROUND_ID}.json"
SETTLEMENT_PAYLOAD_PATH="$STATE_DIR/job-${JOB_ID}-settlement.json"

capture_json "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID" "$job_json_path"
capture_json "$ORCHESTRATOR_BASE_URL/rounds/$ROUND_ID" "$round_json_path"
job_outcome=$(cat "$job_json_path" | json_get offchain_status)
[ "$job_outcome" = "ready_for_attestation" ] || die "public finalization requires off-chain status ready_for_attestation, got $job_outcome"

escrow_balance_wei=$(cat "$job_json_path" | json_get escrow_balance_wei)
split_json=$("$PYTHON_BIN" -m shared.python.public_demo split --escrow-balance-wei "$escrow_balance_wei")
PROVIDER_PAYOUT_WEI=$(printf '%s' "$split_json" | json_get provider_payout_wei)
REQUESTER_REFUND_WEI=$(printf '%s' "$split_json" | json_get requester_refund_wei)

"$PYTHON_BIN" -m shared.python.public_demo settlement \
  --network "$PUBLIC_NETWORK" \
  --chain-id "$PUBLIC_CHAIN_ID" \
  --contract-address "$CONTRACT_ADDRESS" \
  --job-json "$job_json_path" \
  --round-json "$round_json_path" \
  --attestation-hash "$ATTESTATION_HASH" \
  --provider-payout-wei "$PROVIDER_PAYOUT_WEI" \
  --requester-refund-wei "$REQUESTER_REFUND_WEI" >"$SETTLEMENT_PAYLOAD_PATH"

SETTLEMENT_HASH=$("$PYTHON_BIN" -c 'import json,sys; print(json.load(open(sys.argv[1]))["hash"])' "$SETTLEMENT_PAYLOAD_PATH")
onchain_job=$("$PYTHON_BIN" -m shared.python.public_demo onchain-job \
  --rpc-url "$PUBLIC_RPC_URL" \
  --contract-address "$CONTRACT_ADDRESS" \
  --job-id "$JOB_ID")
existing_hash=$(printf '%s' "$onchain_job" | json_get settlement_hash)
existing_status=$(printf '%s' "$onchain_job" | json_get status)
if [ -n "$existing_hash" ]; then
  [ "$existing_hash" = "$SETTLEMENT_HASH" ] || die "on-chain settlement hash mismatch: expected $SETTLEMENT_HASH, got $existing_hash"
  if [ "$existing_status" = "finalized" ]; then
    log "finalization already present on-chain"
    write_state
    log "next step: make public-withdraw"
    exit 0
  fi
fi

log "finalizing public job $JOB_ID with provider payout $PROVIDER_PAYOUT_WEI and requester refund $REQUESTER_REFUND_WEI"
FINALIZATION_TX_HASH=$(send_tx_async "$CONTRACT_ADDRESS" \
  "finalizeJob(uint256,uint256,uint256,bytes32)" \
  "$JOB_ID" \
  "$PROVIDER_PAYOUT_WEI" \
  "$REQUESTER_REFUND_WEI" \
  "$SETTLEMENT_HASH" \
  --rpc-url "$PUBLIC_RPC_URL" \
  --private-key "$ATTESTOR_PRIVATE_KEY")
wait_for_receipt_json "$FINALIZATION_TX_HASH" >/dev/null

curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/jobs/sync" >/dev/null
onchain_job=$("$PYTHON_BIN" -m shared.python.public_demo onchain-job \
  --rpc-url "$PUBLIC_RPC_URL" \
  --contract-address "$CONTRACT_ADDRESS" \
  --job-id "$JOB_ID")
final_status=$(printf '%s' "$onchain_job" | json_get status)
final_hash=$(printf '%s' "$onchain_job" | json_get settlement_hash)
[ "$final_status" = "finalized" ] || die "expected finalized on-chain status, got $final_status"
[ "$final_hash" = "$SETTLEMENT_HASH" ] || die "settlement hash was not persisted on-chain"

write_state
log "job $JOB_ID finalized"
log "next step: make public-withdraw"
