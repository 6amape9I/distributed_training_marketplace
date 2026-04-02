#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/public-common.sh
source "$SCRIPT_DIR/public-common.sh"

require_public_prereqs
require_cmd forge
require_env PUBLIC_RPC_URL
require_env DEPLOYER_PRIVATE_KEY
require_env REQUESTER_PRIVATE_KEY
require_env PROVIDER_PRIVATE_KEY
require_env ATTESTOR_PRIVATE_KEY

ensure_addresses
validate_rpc_chain

log "network: $PUBLIC_NETWORK"
log "chain id: $PUBLIC_CHAIN_ID"
log "deployer address: $DEPLOYER_ADDRESS"
log "requester address: $REQUESTER_ADDRESS"
log "provider address: $PROVIDER_ADDRESS"
log "attestor address: $ATTESTOR_ADDRESS"
log "orchestrator base url: $ORCHESTRATOR_BASE_URL"
