# Contracts Workspace

This directory contains the canonical Foundry workspace for the Stage 1 trust layer.

## Commands
Run these commands from `contracts/` unless noted otherwise.

```bash
forge build
forge test
forge fmt
anvil
forge script script/DeployLocal.s.sol:DeployLocalScript \
  --rpc-url http://127.0.0.1:8545 \
  --broadcast \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
forge script script/DeployPublic.s.sol:DeployPublicScript \
  --rpc-url "$PUBLIC_RPC_URL" \
  --broadcast \
  --private-key "$DEPLOYER_PRIVATE_KEY"
```

If you run the deploy command from the repository root instead, use:

```bash
cd contracts && forge script script/DeployLocal.s.sol:DeployLocalScript \
  --rpc-url http://127.0.0.1:8545 \
  --broadcast \
  --private-key ${DEPLOYER_PRIVATE_KEY:-0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80}
```

For the Stage 7 public path, use `script/DeployPublic.s.sol:DeployPublicScript` together with the helper command `make public-deploy` from the repository root.

## Responsibilities
The contract models a generic marketplace lifecycle:
- create a job;
- fund escrow;
- submit an attestation;
- finalize settlement;
- withdraw payout or refund.

The ABI intentionally avoids FL-specific vocabulary so later protocols can reuse the same trust layer.
