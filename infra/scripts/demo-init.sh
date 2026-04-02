#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=infra/scripts/demo-common.sh
source "$SCRIPT_DIR/demo-common.sh"

require_demo_prereqs

wait_for_http_ok "$ORCHESTRATOR_BASE_URL/health"
wait_for_service_health anvil

log "deploying marketplace contract to the fresh local chain"
compose_cmd exec -T anvil sh -lc "forge script script/DeployLocal.s.sol:DeployLocalScript --rpc-url http://127.0.0.1:8545 --broadcast --private-key $DEPLOYER_PRIVATE_KEY"

code=$(compose_cmd exec -T anvil sh -lc "cast code $MARKETPLACE_CONTRACT_ADDRESS --rpc-url http://127.0.0.1:8545" | tr -d '\r')
[ "$code" != "0x" ] || die "no code found at expected marketplace address $MARKETPLACE_CONTRACT_ADDRESS; run make demo-clean and try again"

next_job_id=$(compose_cmd exec -T anvil sh -lc "cast call $MARKETPLACE_CONTRACT_ADDRESS 'nextJobId()(uint256)' --rpc-url http://127.0.0.1:8545" | tr -d '[:space:]\r')
[ "$next_job_id" = "1" ] || die "expected fresh chain with nextJobId=1, got $next_job_id. Run make demo-clean and retry"

log "creating and funding demo job 1 on-chain"
compose_cmd exec -T anvil sh -lc "cast send $MARKETPLACE_CONTRACT_ADDRESS 'createJob(address,address,uint256,bytes32)' $PROVIDER_ADDRESS $ATTESTOR_ADDRESS $JOB_ESCROW_WEI $JOB_SPEC_HASH --rpc-url http://127.0.0.1:8545 --private-key $DEPLOYER_PRIVATE_KEY >/dev/null"
compose_cmd exec -T anvil sh -lc "cast send $MARKETPLACE_CONTRACT_ADDRESS 'fundJob(uint256)' 1 --value $JOB_ESCROW_WEI --rpc-url http://127.0.0.1:8545 --private-key $DEPLOYER_PRIVATE_KEY >/dev/null"

log "syncing on-chain job into orchestrator"
curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/jobs/sync" >/dev/null

log "waiting for trainers and evaluator to register"
start_ts=$(date +%s)
while true; do
  nodes_json=$(curl -fsS "$ORCHESTRATOR_BASE_URL/nodes")
  online_count=$(printf '%s' "$nodes_json" | python3 -c 'import json, sys; nodes = json.load(sys.stdin); expected = {"trainer-1", "trainer-2", "evaluator-1"}; online = {node["node_id"] for node in nodes if node["status"] == "online"}; print(1 if expected.issubset(online) else 0)')
  if [ "$online_count" = "1" ]; then
    break
  fi
  if [ $(( $(date +%s) - start_ts )) -ge "$DEMO_TIMEOUT_SECONDS" ]; then
    die "timed out waiting for trainer/evaluator nodes to become online"
  fi
  sleep 2
done

log "moving job into scheduling"
for _ in 1 2 3; do
  curl -fsS -X POST "$ORCHESTRATOR_BASE_URL/internal/lifecycle/reconcile" >/dev/null
  job_status=$(curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/1" | json_get offchain_status)
  if [ "$job_status" = "scheduling" ]; then
    break
  fi
  sleep 1
done

job_status=$(curl -fsS "$ORCHESTRATOR_BASE_URL/jobs/1" | json_get offchain_status)
[ "$job_status" = "scheduling" ] || die "expected job 1 to reach scheduling, got $job_status"

CONTRACT_ADDRESS=$MARKETPLACE_CONTRACT_ADDRESS
JOB_ID=1
ROUND_ID=
write_state

log "demo state written to $(print_state_path)"
log "next step: make demo-start-flow"
