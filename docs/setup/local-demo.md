# Local Demo

## Contract-local smoke path
1. Start a local chain:
   ```bash
   anvil
   ```
2. In another shell, deploy the marketplace:
   ```bash
   cd contracts
   forge script script/DeployLocal.s.sol:DeployLocalScript --rpc-url http://127.0.0.1:8545 --broadcast
   ```
3. Run the unit suite:
   ```bash
   forge test
   ```
4. Optionally use `cast` to inspect the deployed contract or replay the transactions shown in the broadcast log.

## What this proves
The smoke path validates the Stage 1 trust layer in isolation: deployment, job lifecycle state transitions, and settlement withdrawals.
