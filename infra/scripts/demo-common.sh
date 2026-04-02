#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
COMPOSE_FILE="$ROOT_DIR/infra/compose/compose.demo.yml"
STATE_DIR="$ROOT_DIR/tmp/demo-state"
STATE_FILE="$STATE_DIR/current-run.env"

MARKETPLACE_CONTRACT_ADDRESS=${MARKETPLACE_CONTRACT_ADDRESS:-0x5FbDB2315678afecb367f032d93F642f64180aa3}
DEPLOYER_PRIVATE_KEY=${DEPLOYER_PRIVATE_KEY:-0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80}
PROVIDER_ADDRESS=${PROVIDER_ADDRESS:-0x70997970C51812dc3A010C7d01b50e0d17dc79C8}
ATTESTOR_ADDRESS=${ATTESTOR_ADDRESS:-0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC}
JOB_ESCROW_WEI=${JOB_ESCROW_WEI:-1000000000000000000}
JOB_SPEC_HASH=${JOB_SPEC_HASH:-0x1111111111111111111111111111111111111111111111111111111111111111}
CHAIN_RPC_URL=${CHAIN_RPC_URL:-http://127.0.0.1:8545}
ORCHESTRATOR_BASE_URL=${ORCHESTRATOR_BASE_URL:-http://127.0.0.1:8000}
DEMO_TIMEOUT_SECONDS=${DEMO_TIMEOUT_SECONDS:-180}
HOST_UID=${HOST_UID:-$(id -u)}
HOST_GID=${HOST_GID:-$(id -g)}

export HOST_UID
export HOST_GID


log() {
  printf '[demo] %s\n' "$*"
}


die() {
  printf '[demo] ERROR: %s\n' "$*" >&2
  exit 1
}


require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}


require_demo_prereqs() {
  require_cmd docker
  require_cmd curl
  require_cmd python3
  docker compose version >/dev/null 2>&1 || die "docker compose is not available"
}


require_host_port_free() {
  local port=$1
  python3 - "$port" <<'PY' || die "required host port $port is already in use"
import socket
import sys

port = int(sys.argv[1])
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.bind(("0.0.0.0", port))
except OSError:
    raise SystemExit(1)
finally:
    sock.close()
PY
}


compose_cmd() {
  HOST_UID="$HOST_UID" HOST_GID="$HOST_GID" docker compose -f "$COMPOSE_FILE" "$@"
}


wait_for_service_health() {
  local service=$1
  local timeout=${2:-$DEMO_TIMEOUT_SECONDS}
  local start_ts
  start_ts=$(date +%s)

  while true; do
    local container_id
    container_id=$(compose_cmd ps -q "$service")
    if [ -n "$container_id" ]; then
      local status
      status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)
      if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
        return 0
      fi
    fi

    if [ $(( $(date +%s) - start_ts )) -ge "$timeout" ]; then
      die "timed out waiting for service '$service' to become healthy"
    fi
    sleep 2
  done
}


wait_for_http_ok() {
  local url=$1
  local timeout=${2:-$DEMO_TIMEOUT_SECONDS}
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
  python3 -c '
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
  python3 -m json.tool
}


write_state() {
  mkdir -p "$STATE_DIR"
  cat >"$STATE_FILE" <<EOF
CONTRACT_ADDRESS=${CONTRACT_ADDRESS:-}
JOB_ID=${JOB_ID:-}
ROUND_ID=${ROUND_ID:-}
EOF
}


load_state() {
  [ -f "$STATE_FILE" ] || die "demo state file not found: $STATE_FILE. Run demo-init first."
  # shellcheck disable=SC1090
  source "$STATE_FILE"
}


print_state_path() {
  printf '%s\n' "$STATE_FILE"
}
