# ADR 0001: Keep heavy ML logic off-chain

## Status
Accepted

## Context
The MVP must prove a distributed training marketplace without forcing expensive or protocol-specific ML execution into smart contracts.

## Decision
Use the blockchain only for job registration, escrow, attestations, finalization, and transparent withdrawals. Keep training, aggregation, evaluation, artifact handling, and node coordination off-chain.

## Consequences
- Stage 1 contracts stay generic and future-proof.
- Off-chain services can start with a FedAvg-like flow later without coupling the contract ABI to one protocol.
- Security and economic review stays focused on settlement logic instead of unverifiable ML behavior.
