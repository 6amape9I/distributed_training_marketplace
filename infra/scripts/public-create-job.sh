#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/public-common.sh
source "$SCRIPT_DIR/public-common.sh"

require_public_prereqs
load_state
require_env PUBLIC_RPC_URL
require_env REQUESTER_PRIVATE_KEY

ensure_addresses
validate_rpc_chain
require_env REQUESTER_ADDRESS
require_env PROVIDER_ADDRESS
require_env ATTESTOR_ADDRESS
[ -n "${CONTRACT_ADDRESS:-}" ] || die "CONTRACT_ADDRESS is missing from public state. Run make public-deploy first."
[ -z "${JOB_ID:-}" ] || die "JOB_ID is already set to $JOB_ID. Remove tmp/public-state if you want a fresh run."

JOB_ID=$(cast call "$CONTRACT_ADDRESS" "nextJobId()(uint256)" --rpc-url "$PUBLIC_RPC_URL" | tr -d '\r[:space:]')
log "creating public job $JOB_ID on $PUBLIC_NETWORK"
JOB_CREATE_TX_HASH=$(send_tx_async "$CONTRACT_ADDRESS" \
  "createJob(address,address,uint256,bytes32)" \
  "$PROVIDER_ADDRESS" \
  "$ATTESTOR_ADDRESS" \
  "$JOB_ESCROW_WEI" \
  "$JOB_SPEC_HASH" \
  --rpc-url "$PUBLIC_RPC_URL" \
  --private-key "$REQUESTER_PRIVATE_KEY")
wait_for_receipt_json "$JOB_CREATE_TX_HASH" >/dev/null

job_snapshot=$("$PYTHON_BIN" -m shared.python.public_demo onchain-job \
  --rpc-url "$PUBLIC_RPC_URL" \
  --contract-address "$CONTRACT_ADDRESS" \
  --job-id "$JOB_ID")
status=$(printf '%s' "$job_snapshot" | json_get status)
[ "$status" = "open" ] || die "expected new on-chain job to be open, got $status"

write_state
log "job $JOB_ID created"
log "next step: make public-fund-job"
