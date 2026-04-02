#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
STATE_DIR="$ROOT_DIR/tmp/public-state"
STATE_FILE="$STATE_DIR/current-run.env"
DEPLOYMENTS_DIR="$STATE_DIR/deployments"
PYTHON_BIN=${PYTHON_BIN:-$ROOT_DIR/.venv/bin/python}

PUBLIC_NETWORK=${PUBLIC_NETWORK:-base-sepolia}
PUBLIC_CHAIN_ID=${PUBLIC_CHAIN_ID:-84532}
PUBLIC_RPC_URL=${PUBLIC_RPC_URL:-}
PUBLIC_CONFIRMATIONS=${PUBLIC_CONFIRMATIONS:-1}
PUBLIC_TIMEOUT_SECONDS=${PUBLIC_TIMEOUT_SECONDS:-300}

ORCHESTRATOR_BASE_URL=${ORCHESTRATOR_BASE_URL:-http://127.0.0.1:8000}
JOB_ESCROW_WEI=${JOB_ESCROW_WEI:-10000000000000000}
JOB_SPEC_HASH=${JOB_SPEC_HASH:-0x1111111111111111111111111111111111111111111111111111111111111111}

DEPLOYER_PRIVATE_KEY=${DEPLOYER_PRIVATE_KEY:-}
REQUESTER_PRIVATE_KEY=${REQUESTER_PRIVATE_KEY:-}
PROVIDER_PRIVATE_KEY=${PROVIDER_PRIVATE_KEY:-}
ATTESTOR_PRIVATE_KEY=${ATTESTOR_PRIVATE_KEY:-}

DEPLOYER_ADDRESS=${DEPLOYER_ADDRESS:-}
REQUESTER_ADDRESS=${REQUESTER_ADDRESS:-}
PROVIDER_ADDRESS=${PROVIDER_ADDRESS:-}
ATTESTOR_ADDRESS=${ATTESTOR_ADDRESS:-}

CONTRACT_ADDRESS=${CONTRACT_ADDRESS:-}
DEPLOYMENT_TX_HASH=${DEPLOYMENT_TX_HASH:-}
JOB_ID=${JOB_ID:-}
JOB_CREATE_TX_HASH=${JOB_CREATE_TX_HASH:-}
JOB_FUND_TX_HASH=${JOB_FUND_TX_HASH:-}
ROUND_ID=${ROUND_ID:-}
OFFCHAIN_FINAL_STATUS=${OFFCHAIN_FINAL_STATUS:-}
ATT_PAYLOAD_PATH=${ATT_PAYLOAD_PATH:-}
ATTESTATION_HASH=${ATTESTATION_HASH:-}
ATTESTATION_TX_HASH=${ATTESTATION_TX_HASH:-}
SETTLEMENT_PAYLOAD_PATH=${SETTLEMENT_PAYLOAD_PATH:-}
SETTLEMENT_HASH=${SETTLEMENT_HASH:-}
FINALIZATION_TX_HASH=${FINALIZATION_TX_HASH:-}
PROVIDER_PAYOUT_WEI=${PROVIDER_PAYOUT_WEI:-}
REQUESTER_REFUND_WEI=${REQUESTER_REFUND_WEI:-}
PROVIDER_WITHDRAW_TX_HASH=${PROVIDER_WITHDRAW_TX_HASH:-}
REQUESTER_WITHDRAW_TX_HASH=${REQUESTER_WITHDRAW_TX_HASH:-}


log() {
  printf '[public] %s\n' "$*"
}


die() {
  printf '[public] ERROR: %s\n' "$*" >&2
  exit 1
}


require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}


require_python() {
  if [ -x "$PYTHON_BIN" ]; then
    return 0
  fi
  PYTHON_BIN=$(command -v python3 || true)
  [ -n "$PYTHON_BIN" ] || die "missing python3"
}


require_public_prereqs() {
  require_cmd cast
  require_cmd curl
  require_python
}


derive_address_from_key() {
  local private_key=$1
  cast wallet address --private-key "$private_key" | tr -d '\r[:space:]'
}


ensure_addresses() {
  if [ -z "$DEPLOYER_ADDRESS" ] && [ -n "$DEPLOYER_PRIVATE_KEY" ]; then
    DEPLOYER_ADDRESS=$(derive_address_from_key "$DEPLOYER_PRIVATE_KEY")
  fi
  if [ -z "$REQUESTER_ADDRESS" ] && [ -n "$REQUESTER_PRIVATE_KEY" ]; then
    REQUESTER_ADDRESS=$(derive_address_from_key "$REQUESTER_PRIVATE_KEY")
  fi
  if [ -z "$PROVIDER_ADDRESS" ] && [ -n "$PROVIDER_PRIVATE_KEY" ]; then
    PROVIDER_ADDRESS=$(derive_address_from_key "$PROVIDER_PRIVATE_KEY")
  fi
  if [ -z "$ATTESTOR_ADDRESS" ] && [ -n "$ATTESTOR_PRIVATE_KEY" ]; then
    ATTESTOR_ADDRESS=$(derive_address_from_key "$ATTESTOR_PRIVATE_KEY")
  fi
}


require_env() {
  local name=$1
  [ -n "${!name:-}" ] || die "missing required environment variable: $name"
}


validate_rpc_chain() {
  require_env PUBLIC_RPC_URL
  local actual_chain_id
  actual_chain_id=$(cast chain-id --rpc-url "$PUBLIC_RPC_URL" | tr -d '\r[:space:]')
  [ "$actual_chain_id" = "$PUBLIC_CHAIN_ID" ] || die "expected chain id $PUBLIC_CHAIN_ID, got $actual_chain_id"
}


wait_for_http_ok() {
  local url=$1
  local timeout=${2:-$PUBLIC_TIMEOUT_SECONDS}
  local start_ts
  start_ts=$(date +%s)

  while true; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    if [ $(( $(date +%s) - start_ts )) -ge "$timeout" ]; then
      die "timed out waiting for HTTP endpoint: $url"
    fi
    sleep 2
  done
}


json_get() {
  local path=$1
  "$PYTHON_BIN" -c '
import json
import sys

path = sys.argv[1]
data = json.load(sys.stdin)

if path:
    for part in path.split("."):
        if part.isdigit():
            data = data[int(part)]
        else:
            data = data[part]

if isinstance(data, (dict, list)):
    print(json.dumps(data))
elif data is None:
    print("")
else:
    print(data)
' "$path"
}


pretty_json() {
  "$PYTHON_BIN" -m json.tool
}


write_state() {
  mkdir -p "$STATE_DIR"
  {
    printf 'PUBLIC_NETWORK=%q\n' "$PUBLIC_NETWORK"
    printf 'PUBLIC_CHAIN_ID=%q\n' "$PUBLIC_CHAIN_ID"
    printf 'PUBLIC_RPC_URL=%q\n' "$PUBLIC_RPC_URL"
    printf 'ORCHESTRATOR_BASE_URL=%q\n' "$ORCHESTRATOR_BASE_URL"
    printf 'DEPLOYER_ADDRESS=%q\n' "$DEPLOYER_ADDRESS"
    printf 'REQUESTER_ADDRESS=%q\n' "$REQUESTER_ADDRESS"
    printf 'PROVIDER_ADDRESS=%q\n' "$PROVIDER_ADDRESS"
    printf 'ATTESTOR_ADDRESS=%q\n' "$ATTESTOR_ADDRESS"
    printf 'CONTRACT_ADDRESS=%q\n' "$CONTRACT_ADDRESS"
    printf 'DEPLOYMENT_TX_HASH=%q\n' "$DEPLOYMENT_TX_HASH"
    printf 'JOB_ID=%q\n' "$JOB_ID"
    printf 'JOB_CREATE_TX_HASH=%q\n' "$JOB_CREATE_TX_HASH"
    printf 'JOB_FUND_TX_HASH=%q\n' "$JOB_FUND_TX_HASH"
    printf 'ROUND_ID=%q\n' "$ROUND_ID"
    printf 'OFFCHAIN_FINAL_STATUS=%q\n' "$OFFCHAIN_FINAL_STATUS"
    printf 'ATT_PAYLOAD_PATH=%q\n' "$ATT_PAYLOAD_PATH"
    printf 'ATTESTATION_HASH=%q\n' "$ATTESTATION_HASH"
    printf 'ATTESTATION_TX_HASH=%q\n' "$ATTESTATION_TX_HASH"
    printf 'SETTLEMENT_PAYLOAD_PATH=%q\n' "$SETTLEMENT_PAYLOAD_PATH"
    printf 'SETTLEMENT_HASH=%q\n' "$SETTLEMENT_HASH"
    printf 'FINALIZATION_TX_HASH=%q\n' "$FINALIZATION_TX_HASH"
    printf 'PROVIDER_PAYOUT_WEI=%q\n' "$PROVIDER_PAYOUT_WEI"
    printf 'REQUESTER_REFUND_WEI=%q\n' "$REQUESTER_REFUND_WEI"
    printf 'PROVIDER_WITHDRAW_TX_HASH=%q\n' "$PROVIDER_WITHDRAW_TX_HASH"
    printf 'REQUESTER_WITHDRAW_TX_HASH=%q\n' "$REQUESTER_WITHDRAW_TX_HASH"
  } >"$STATE_FILE"
}


load_state() {
  [ -f "$STATE_FILE" ] || die "public state file not found: $STATE_FILE. Run the public setup steps first."
  # shellcheck disable=SC1090
  source "$STATE_FILE"
}


print_state_path() {
  printf '%s\n' "$STATE_FILE"
}


send_tx_async() {
  cast send "$@" --async | tr -d '\r[:space:]'
}


wait_for_receipt_json() {
  local tx_hash=$1
  cast receipt "$tx_hash" --rpc-url "$PUBLIC_RPC_URL" --confirmations "$PUBLIC_CONFIRMATIONS" --json
}


capture_json() {
  local url=$1
  local path=$2
  curl -fsS "$url" >"$path"
}


render_tx_summary() {
  local tx_hash=$1
  [ -n "$tx_hash" ] || return 0
  local receipt_json
  receipt_json=$(wait_for_receipt_json "$tx_hash")
  printf '%s\n' "$receipt_json" | "$PYTHON_BIN" -c '
import json
import sys

receipt = json.load(sys.stdin)
summary = {
    "transactionHash": receipt.get("transactionHash"),
    "status": receipt.get("status"),
    "blockNumber": receipt.get("blockNumber"),
    "from": receipt.get("from"),
    "to": receipt.get("to"),
    "contractAddress": receipt.get("contractAddress"),
}
print(json.dumps(summary, indent=2, sort_keys=True))
'
}
