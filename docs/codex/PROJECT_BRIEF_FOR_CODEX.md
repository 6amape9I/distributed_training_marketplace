# Project Brief for Codex

## Project
**distributed_training_marketplace**

## Mission
Build a clean new MVP repository for a **distributed training marketplace with an on-chain trust/settlement layer and an off-chain execution layer**.

This is **not** a blockchain that trains models on-chain and **not** a “useful PoW Bitcoin replacement”.
The blockchain is used only for:
- job registration;
- escrow / settlement;
- status attestations;
- finalization;
- transparent payouts / refunds.

All heavy work stays off-chain:
- training;
- model updates;
- checkpoint handling;
- node selection;
- aggregation;
- evaluation;
- artifact storage.

## Strategic goal
The repository must be designed so that the first protocol implementation can be **FL/FedAvg-like for MVP**, while the architecture remains **protocol-agnostic**.

We must be able later to replace or extend the protocol with:
- FedProx;
- hierarchical FL;
- hybrid orchestrated protocols;
- gossip/P2P-inspired variants;
- adapter-based or other lightweight distributed training variants.

## What Codex is allowed to optimize for
Codex may optimize for:
- correctness;
- clean modular architecture;
- reproducibility;
- local developer experience;
- a fast path to a working vertical slice.

Codex must **not** optimize for:
- flashy UI;
- tokenomics;
- premature decentralization;
- overengineering for large models;
- advanced byzantine defenses in MVP.

## Core architectural decision
Create a **new repository structure from scratch**. The previous mock repository is only a reference artifact and must not dictate the architecture.

## MVP demonstration target
MVP must demonstrate:
1. a job is created and funded on-chain;
2. an off-chain orchestrator discovers the job;
3. 2–4 trainer agents perform local training on a simple dataset;
4. the orchestrator aggregates updates;
5. an evaluator validates the resulting model;
6. a final result attestation is written on-chain;
7. the job is finalized and payout/refund occurs.

## Demo scope
Preferred first demo:
- dataset: `Breast Cancer Wisconsin` (fallback: `Iris`);
- model: a small PyTorch MLP or another intentionally simple replaceable baseline;
- topology: 1 orchestrator, 2–4 trainer agents, 1 evaluator agent;
- environment: first on one machine via multiple processes/containers, then optionally on several real machines.

## Non-goals of MVP
Do not implement yet:
- custom token;
- DAO/governance;
- slashing/staking economics;
- trustless training verification;
- advanced reputation;
- byzantine-resistant aggregation;
- full P2P coordination without orchestrator;
- production UI.

## Technology direction
- **Ubuntu** as the target development OS.
- Smart contracts: **Solidity + Foundry + OpenZeppelin**.
- Backend/orchestrator: **Python 3.12 + FastAPI + SQLAlchemy + Alembic + web3.py**.
- Artifact storage: local filesystem in dev mode, designed for MinIO/S3 later.
- Database: SQLite in dev bootstrap, PostgreSQL-ready abstractions.
- Containers: Docker Compose.

## What must be true after Stage 1
After the first implementation stage, the repository must already contain:
- a clean structure;
- documented architecture;
- a local dev environment;
- a working smart-contract trust layer with tests;
- enough scaffolding so off-chain services can be connected next without restructuring contracts.

## Quality bar
Every change should move the project toward a clean long-term architecture.
Temporary MVP shortcuts are allowed only when they:
1. are isolated;
2. are documented;
3. do not leak into core abstractions.
