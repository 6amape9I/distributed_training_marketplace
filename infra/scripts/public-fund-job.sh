#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/public-common.sh
source "$SCRIPT_DIR/public-common.sh"

require_public_prereqs
load_state
require_env PUBLIC_RPC_URL
require_env REQUESTER_PRIVATE_KEY

validate_rpc_chain
[ -n "${CONTRACT_ADDRESS:-}" ] || die "missing CONTRACT_ADDRESS in public state"
[ -n "${JOB_ID:-}" ] || die "missing JOB_ID in public state"

log "funding public job $JOB_ID with $JOB_ESCROW_WEI wei"
JOB_FUND_TX_HASH=$(send_tx_async "$CONTRACT_ADDRESS" \
  "fundJob(uint256)" \
  "$JOB_ID" \
  --value "$JOB_ESCROW_WEI" \
  --rpc-url "$PUBLIC_RPC_URL" \
  --private-key "$REQUESTER_PRIVATE_KEY")
wait_for_receipt_json "$JOB_FUND_TX_HASH" >/dev/null

job_snapshot=$("$PYTHON_BIN" -m shared.python.public_demo onchain-job \
  --rpc-url "$PUBLIC_RPC_URL" \
  --contract-address "$CONTRACT_ADDRESS" \
  --job-id "$JOB_ID")
status=$(printf '%s' "$job_snapshot" | json_get status)
escrow_balance=$(printf '%s' "$job_snapshot" | json_get escrow_balance_wei)
[ "$status" = "funded" ] || die "expected funded on-chain job, got $status"
[ "$escrow_balance" = "$JOB_ESCROW_WEI" ] || die "expected escrow balance $JOB_ESCROW_WEI, got $escrow_balance"

write_state
log "job $JOB_ID funded"
log "next step: make public-sync-job"
