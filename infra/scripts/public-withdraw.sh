#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/public-common.sh
source "$SCRIPT_DIR/public-common.sh"

mode=${1:-all}

require_public_prereqs
load_state
require_env PUBLIC_RPC_URL

[ -n "${JOB_ID:-}" ] || die "missing JOB_ID in public state"
[ -n "${FINALIZATION_TX_HASH:-}" ] || die "public withdraw requires a finalized job"

validate_rpc_chain

case "$mode" in
  all|provider|requester)
    ;;
  *)
    die "unsupported withdraw mode: $mode (expected all, provider, or requester)"
    ;;
esac

if [ "$mode" = "all" ] || [ "$mode" = "provider" ]; then
  if [ -n "${PROVIDER_PAYOUT_WEI:-}" ] && [ "$PROVIDER_PAYOUT_WEI" != "0" ]; then
    if [ -z "${PROVIDER_WITHDRAW_TX_HASH:-}" ]; then
      require_env PROVIDER_PRIVATE_KEY
      log "withdrawing provider payout for job $JOB_ID"
      PROVIDER_WITHDRAW_TX_HASH=$(send_tx_async "$CONTRACT_ADDRESS" \
        "withdrawPayout(uint256)" \
        "$JOB_ID" \
        --rpc-url "$PUBLIC_RPC_URL" \
        --private-key "$PROVIDER_PRIVATE_KEY")
      wait_for_receipt_json "$PROVIDER_WITHDRAW_TX_HASH" >/dev/null
    else
      log "provider withdrawal already recorded at $PROVIDER_WITHDRAW_TX_HASH"
    fi
  fi
fi

if [ "$mode" = "all" ] || [ "$mode" = "requester" ]; then
  if [ -n "${REQUESTER_REFUND_WEI:-}" ] && [ "$REQUESTER_REFUND_WEI" != "0" ]; then
    if [ -z "${REQUESTER_WITHDRAW_TX_HASH:-}" ]; then
      require_env REQUESTER_PRIVATE_KEY
      log "withdrawing requester refund for job $JOB_ID"
      REQUESTER_WITHDRAW_TX_HASH=$(send_tx_async "$CONTRACT_ADDRESS" \
        "withdrawRefund(uint256)" \
        "$JOB_ID" \
        --rpc-url "$PUBLIC_RPC_URL" \
        --private-key "$REQUESTER_PRIVATE_KEY")
      wait_for_receipt_json "$REQUESTER_WITHDRAW_TX_HASH" >/dev/null
    else
      log "requester withdrawal already recorded at $REQUESTER_WITHDRAW_TX_HASH"
    fi
  fi
fi

write_state
log "withdraw flow complete"
