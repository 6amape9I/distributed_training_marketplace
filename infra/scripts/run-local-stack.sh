#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
RPC_URL=${CHAIN_RPC_URL:-http://127.0.0.1:8545}

cat <<MSG
Starting Stage 1 local chain at ${RPC_URL}.
Next steps after anvil is up:
  1. cd "$ROOT_DIR/contracts"
  2. forge script script/DeployLocal.s.sol:DeployLocalScript --rpc-url ${RPC_URL} --broadcast
  3. forge test
MSG

exec anvil --host 0.0.0.0 --port 8545
