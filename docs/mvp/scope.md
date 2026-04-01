# MVP Scope

## Included in Stage 1
- repository skeleton aligned with the target structure;
- architecture and setup documentation;
- canonical Foundry workspace with a tested trust layer;
- placeholder orchestrator and agent modules;
- local scripts for environment checks and contract smoke testing.

## Explicitly excluded from Stage 1
- real model training or aggregation;
- evaluator logic beyond typed placeholders;
- tokenomics, staking, or slashing;
- full P2P coordination;
- production UI;
- byzantine-resistant aggregation.

## Allowed shortcuts
- SQLite-ready configuration without a live database migration flow;
- local filesystem artifact paths instead of S3/MinIO;
- static single-provider settlement per job.
