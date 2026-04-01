# Contracts Workspace

This directory contains the canonical Foundry workspace for the Stage 1 trust layer.

## Commands
```bash
forge build
forge test
forge fmt
anvil
forge script script/DeployLocal.s.sol:DeployLocalScript --rpc-url http://127.0.0.1:8545 --broadcast
```

## Responsibilities
The contract models a generic marketplace lifecycle:
- create a job;
- fund escrow;
- submit an attestation;
- finalize settlement;
- withdraw payout or refund.

The ABI intentionally avoids FL-specific vocabulary so later protocols can reuse the same trust layer.
