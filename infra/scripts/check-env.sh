#!/usr/bin/env bash
set -euo pipefail

for cmd in forge anvil cast python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "missing required command: $cmd" >&2
    exit 1
  fi
  echo "found $cmd: $(command -v "$cmd")"
done
