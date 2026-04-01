# Architecture Overview

## Intent
The repository is split into a minimal on-chain trust layer and an off-chain execution layer. This keeps the MVP easy to verify while leaving room for multiple distributed training protocols later.

## On-chain responsibilities
The `contracts/` workspace handles only:
- job registration;
- escrow funding;
- result attestations;
- finalization;
- payout and refund withdrawals.

Contracts must stay protocol-agnostic. They should not mention tensors, gradients, or FL-only settlement concepts.

## Off-chain responsibilities
The orchestrator and agent services are responsible for:
- job discovery;
- trainer selection;
- training execution;
- aggregation;
- evaluation;
- artifact storage.

Stage 1 ships only typed scaffolding for these services so Stage 2 can add runtime logic without restructuring the repository.

## Extension points
Off-chain protocol customization is expressed through six interfaces:
- `TrainingProtocol`
- `AggregationStrategy`
- `EvaluationStrategy`
- `NodeSelectionStrategy`
- `ArtifactRepository`
- `PayoutPolicy`
