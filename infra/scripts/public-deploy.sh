#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/public-common.sh
source "$SCRIPT_DIR/public-common.sh"

require_public_prereqs
require_cmd forge
require_env PUBLIC_RPC_URL
require_env DEPLOYER_PRIVATE_KEY

ensure_addresses
validate_rpc_chain

log "deploying TrainingMarketplace to $PUBLIC_NETWORK"
(
  cd "$ROOT_DIR/contracts"
  forge script script/DeployPublic.s.sol:DeployPublicScript \
    --rpc-url "$PUBLIC_RPC_URL" \
    --broadcast \
    --private-key "$DEPLOYER_PRIVATE_KEY"
)

broadcast_file="$ROOT_DIR/contracts/broadcast/DeployPublic.s.sol/$PUBLIC_CHAIN_ID/run-latest.json"
[ -f "$broadcast_file" ] || die "missing broadcast artifact: $broadcast_file"

mkdir -p "$DEPLOYMENTS_DIR"
deployment_file="$DEPLOYMENTS_DIR/${PUBLIC_NETWORK}.json"
"$PYTHON_BIN" - "$broadcast_file" "$deployment_file" "$PUBLIC_NETWORK" "$PUBLIC_CHAIN_ID" <<'PY'
import json
import sys
from pathlib import Path

broadcast_path = Path(sys.argv[1])
deployment_path = Path(sys.argv[2])
network = sys.argv[3]
chain_id = int(sys.argv[4])
broadcast = json.loads(broadcast_path.read_text(encoding="utf-8"))
tx = broadcast["transactions"][0]

deployment = {
    "network": network,
    "chain_id": chain_id,
    "contract_address": tx["contractAddress"],
    "deployment_tx_hash": tx["hash"],
    "deployer_address": tx["transaction"]["from"],
    "broadcast_path": str(broadcast_path),
}
deployment_path.write_text(json.dumps(deployment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(deployment))
PY

deployment_json=$("$PYTHON_BIN" -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))' "$deployment_file")
CONTRACT_ADDRESS=$(printf '%s' "$deployment_json" | json_get contract_address)
DEPLOYMENT_TX_HASH=$(printf '%s' "$deployment_json" | json_get deployment_tx_hash)
DEPLOYER_ADDRESS=$(printf '%s' "$deployment_json" | json_get deployer_address)

code=$(cast code "$CONTRACT_ADDRESS" --rpc-url "$PUBLIC_RPC_URL" | tr -d '\r[:space:]')
[ "$code" != "0x" ] || die "deployment succeeded but no code found at $CONTRACT_ADDRESS"

JOB_ID=
JOB_CREATE_TX_HASH=
JOB_FUND_TX_HASH=
ROUND_ID=
OFFCHAIN_FINAL_STATUS=
ATT_PAYLOAD_PATH=
ATTESTATION_HASH=
ATTESTATION_TX_HASH=
SETTLEMENT_PAYLOAD_PATH=
SETTLEMENT_HASH=
FINALIZATION_TX_HASH=
PROVIDER_PAYOUT_WEI=
REQUESTER_REFUND_WEI=
PROVIDER_WITHDRAW_TX_HASH=
REQUESTER_WITHDRAW_TX_HASH=
write_state

log "deployment artifact written to $deployment_file"
log "public run state written to $(print_state_path)"
log "next step: make public-create-job"
