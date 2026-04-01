# Domain Model

## Core entities
- `Job`: the marketplace unit created by a requester and executed by a provider.
- `Round`: an off-chain protocol concept retained in docs and future orchestrator code, not in Stage 1 contracts.
- `Submission/Attestation`: a signed or authorized statement that records off-chain progress or a final result hash.
- `Evaluation`: the off-chain decision that determines whether a result is accepted.
- `Settlement`: the final allocation of escrow between provider payout and requester refund.

## Stage 1 contract roles
- `requester`: creates the job and supplies escrow.
- `provider`: eligible recipient of payout after successful finalization.
- `attestor`: independent authority that records a result hash and final settlement decision.

## State model
Stage 1 contract lifecycle:
1. `Open`
2. `Funded`
3. `Attested`
4. `Finalized`

The contract remains intentionally small. Multi-round coordination, trainer sets, and aggregation metadata stay off-chain until later stages.
