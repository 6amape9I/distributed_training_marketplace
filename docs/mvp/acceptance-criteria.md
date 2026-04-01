# Stage 1 Acceptance Criteria

Stage 1 is complete when all of the following are true:
- the repository matches the documented structure and contains the required bootstrap files;
- `contracts/` builds successfully with Foundry;
- contract tests cover creation, funding, attestation, finalization, payouts, refunds, and authorization failures;
- a local deploy script works against `anvil`;
- the contract ABI uses generic marketplace language rather than FL-specific terminology;
- orchestrator and agent placeholders exist with typed extension points for Stage 2;
- a new contributor can follow the documented local contract smoke path.
