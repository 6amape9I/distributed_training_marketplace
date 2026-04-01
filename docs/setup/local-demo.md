# Local Demo

All commands below are written from the repository root unless a line says otherwise.

## Contract-local smoke path
1. Start a local chain:
   ```bash
   anvil
   ```
2. In another shell, deploy the marketplace:
   ```bash
   cd contracts
   forge script script/DeployLocal.s.sol:DeployLocalScript \
     --rpc-url http://127.0.0.1:8545 \
     --broadcast \
     --private-key ${DEPLOYER_PRIVATE_KEY:-0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80}
   ```
   If your current shell is already in `docs/setup/`, use `cd ../../contracts` instead of `cd contracts`.
3. Run the unit suite:
   ```bash
   forge test --root contracts
   ```
4. Optionally verify the deployment:
   ```bash
   cast call <deployed_address> "nextJobId()(uint256)" --rpc-url http://127.0.0.1:8545
   ```

## Common Foundry issue
If Foundry prints `You seem to be using Foundry's default sender`, rerun the deploy command with an explicit signer.

- Local `anvil` default: use `--private-key 0xac0974...ff80`
- Alternative for unlocked local accounts:
  ```bash
  forge script script/DeployLocal.s.sol:DeployLocalScript \
    --rpc-url http://127.0.0.1:8545 \
    --broadcast \
    --unlocked \
    --sender 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
  ```

## What this proves
The smoke path validates the Stage 1 trust layer in isolation: deployment, job lifecycle state transitions, and settlement withdrawals.
