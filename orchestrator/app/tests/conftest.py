from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from orchestrator.app.api.main import create_app
from orchestrator.app.domain.entities import ChainSyncState, Job, JobEventRecord, Node
from orchestrator.app.domain.enums import NodeRole, OffchainJobStatus, OnchainJobStatus
from orchestrator.app.infrastructure.blockchain.types import ChainEvent, ChainJobSnapshot
from orchestrator.app.infrastructure.db.base import Base
from orchestrator.app.infrastructure.settings import Settings


class FakeBlockchainClient:
    def __init__(self) -> None:
        self.events: list[ChainEvent] = []
        self.jobs: dict[int, ChainJobSnapshot] = {}
        self.chain_id = 31337
        self.latest_block = 0

    def add_job(self, job: ChainJobSnapshot) -> None:
        self.jobs[job.job_id] = job

    def add_event(self, event: ChainEvent) -> None:
        self.events.append(event)
        self.latest_block = max(self.latest_block, event.block_number)

    def get_chain_id(self) -> int:
        return self.chain_id

    def get_latest_block(self) -> int:
        return self.latest_block

    def get_status(self) -> dict[str, object]:
        return {
            "reachable": True,
            "chain_id": self.chain_id,
            "latest_block": self.latest_block,
            "rpc_url": "http://fake-chain.local",
        }

    def fetch_events(self, *, from_block: int, to_block: int) -> list[ChainEvent]:
        return sorted(
            [event for event in self.events if from_block <= event.block_number <= to_block],
            key=lambda item: (item.block_number, item.log_index),
        )

    def get_job(self, job_id: int) -> ChainJobSnapshot:
        return self.jobs[job_id]


class InMemoryJobRepository:
    def __init__(self) -> None:
        self.data: dict[int, Job] = {}

    def get(self, job_id: int) -> Job | None:
        return self.data.get(job_id)

    def list(self) -> list[Job]:
        return [self.data[key] for key in sorted(self.data)]

    def list_by_offchain_status(self, status: OffchainJobStatus) -> list[Job]:
        return [job for job in self.list() if job.offchain_status == status]

    def upsert(self, job: Job) -> Job:
        self.data[job.job_id] = job
        return job


class InMemoryNodeRepository:
    def __init__(self) -> None:
        self.data: dict[str, Node] = {}

    def get(self, node_id: str) -> Node | None:
        return self.data.get(node_id)

    def list(self) -> list[Node]:
        return [self.data[key] for key in sorted(self.data)]

    def list_by_role(self, role: NodeRole) -> list[Node]:
        return [node for node in self.list() if node.role == role]

    def upsert(self, node: Node) -> Node:
        self.data[node.node_id] = node
        return node


class InMemorySyncStateRepository:
    def __init__(self) -> None:
        self.data: dict[str, ChainSyncState] = {}

    def get(self, sync_key: str) -> ChainSyncState | None:
        return self.data.get(sync_key)

    def upsert(self, state: ChainSyncState) -> ChainSyncState:
        self.data[state.sync_key] = state
        return state


class InMemoryJobEventRepository:
    def __init__(self) -> None:
        self.events: dict[tuple[str, int], JobEventRecord] = {}

    def exists(self, transaction_hash: str, log_index: int) -> bool:
        return (transaction_hash, log_index) in self.events

    def add(self, event: JobEventRecord) -> JobEventRecord:
        self.events[(event.transaction_hash, event.log_index)] = event
        return event


def build_snapshot(
    *,
    job_id: int = 1,
    onchain_status: OnchainJobStatus = OnchainJobStatus.FUNDED,
    escrow_balance_wei: int = 10,
    attestation_hash: str | None = None,
    settlement_hash: str | None = None,
    provider_payout_wei: int = 0,
    requester_refund_wei: int = 0,
) -> ChainJobSnapshot:
    return ChainJobSnapshot(
        job_id=job_id,
        requester="0x00000000000000000000000000000000000000a1",
        provider="0x00000000000000000000000000000000000000b2",
        attestor="0x00000000000000000000000000000000000000c3",
        target_escrow_wei=10,
        escrow_balance_wei=escrow_balance_wei,
        job_spec_hash="0x" + "1" * 64,
        attestation_hash=attestation_hash,
        settlement_hash=settlement_hash,
        provider_payout_wei=provider_payout_wei,
        requester_refund_wei=requester_refund_wei,
        onchain_status=onchain_status,
    )


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        host="127.0.0.1",
        port=8000,
        chain_rpc_url="http://fake-chain.local",
        chain_id=31337,
        marketplace_contract_address="0x0000000000000000000000000000000000000001",
        database_url=f"sqlite:///{tmp_path / 'orchestrator-test.db'}",
        artifact_root=str(tmp_path / "artifacts"),
        sync_start_block=0,
        sync_batch_size=100,
        node_stale_after_seconds=60,
    )


@pytest.fixture
def fake_blockchain() -> FakeBlockchainClient:
    return FakeBlockchainClient()


@pytest.fixture
def app(test_settings: Settings, fake_blockchain: FakeBlockchainClient):
    app = create_app(settings=test_settings, blockchain_client=fake_blockchain)
    Base.metadata.create_all(app.state.container.engine)
    return app
