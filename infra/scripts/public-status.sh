#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/public-common.sh
source "$SCRIPT_DIR/public-common.sh"

require_public_prereqs
ensure_addresses

printf '[public] network\n'
printf '{\n'
printf '  "network": "%s",\n' "$PUBLIC_NETWORK"
printf '  "chain_id": "%s",\n' "$PUBLIC_CHAIN_ID"
printf '  "rpc_url": "%s",\n' "$PUBLIC_RPC_URL"
printf '  "state_file": "%s"\n' "$STATE_FILE"
printf '}\n\n'

if [ -f "$STATE_FILE" ]; then
  load_state
  printf '[public] current state\n'
  cat "$STATE_FILE"
  printf '\n'
fi

if [ -n "${PUBLIC_RPC_URL:-}" ]; then
  printf '[public] chain id from rpc\n'
  cast chain-id --rpc-url "$PUBLIC_RPC_URL" | tr -d '\r'
  printf '\n\n'
fi

if [ -n "${ORCHESTRATOR_BASE_URL:-}" ] && curl -fsS "$ORCHESTRATOR_BASE_URL/health" >/dev/null 2>&1; then
  printf '[public] orchestrator /health\n'
  curl -fsS "$ORCHESTRATOR_BASE_URL/health" | pretty_json
  printf '\n\n'

  printf '[public] orchestrator /status\n'
  curl -fsS "$ORCHESTRATOR_BASE_URL/status" | pretty_json
  printf '\n\n'

  if [ -n "${JOB_ID:-}" ]; then
    printf '[public] job %s details\n' "$JOB_ID"
    curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID" | pretty_json
    printf '\n\n'

    printf '[public] job %s rounds\n' "$JOB_ID"
    curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/rounds" | pretty_json
    printf '\n\n'

    printf '[public] job %s training tasks\n' "$JOB_ID"
    curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/training-tasks" | pretty_json
    printf '\n\n'

    printf '[public] job %s evaluation tasks\n' "$JOB_ID"
    curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/$JOB_ID/evaluation-tasks" | pretty_json
    printf '\n\n'
  fi
fi

if [ -n "${CONTRACT_ADDRESS:-}" ] && [ -n "${JOB_ID:-}" ] && [ -n "${PUBLIC_RPC_URL:-}" ]; then
  printf '[public] on-chain job %s\n' "$JOB_ID"
  "$PYTHON_BIN" -m shared.python.public_demo onchain-job \
    --rpc-url "$PUBLIC_RPC_URL" \
    --contract-address "$CONTRACT_ADDRESS" \
    --job-id "$JOB_ID" | pretty_json
  printf '\n\n'
fi

for label in DEPLOYMENT_TX_HASH JOB_CREATE_TX_HASH JOB_FUND_TX_HASH ATTESTATION_TX_HASH FINALIZATION_TX_HASH PROVIDER_WITHDRAW_TX_HASH REQUESTER_WITHDRAW_TX_HASH; do
  tx_hash=${!label:-}
  if [ -n "$tx_hash" ] && [ -n "${PUBLIC_RPC_URL:-}" ]; then
    printf '[public] %s\n' "$label"
    render_tx_summary "$tx_hash"
    printf '\n\n'
  fi
done

if [ -n "${REQUESTER_ADDRESS:-}" ] && [ -n "${PUBLIC_RPC_URL:-}" ]; then
  printf '[public] requester balance\n'
  cast balance "$REQUESTER_ADDRESS" --ether --rpc-url "$PUBLIC_RPC_URL"
  printf '\n\n'
fi

if [ -n "${PROVIDER_ADDRESS:-}" ] && [ -n "${PUBLIC_RPC_URL:-}" ]; then
  printf '[public] provider balance\n'
  cast balance "$PROVIDER_ADDRESS" --ether --rpc-url "$PUBLIC_RPC_URL"
  printf '\n\n'
fi
