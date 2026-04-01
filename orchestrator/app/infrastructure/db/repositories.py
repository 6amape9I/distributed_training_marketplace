from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from orchestrator.app.domain.entities import ChainSyncState, Job, JobEventRecord, Node
from orchestrator.app.domain.enums import NodeRole, NodeStatus, OffchainJobStatus, OnchainJobStatus
from orchestrator.app.infrastructure.db.models import ChainSyncStateModel, JobEventModel, JobModel, NodeModel


def _job_to_entity(model: JobModel) -> Job:
    return Job(
        job_id=model.job_id,
        requester=model.requester,
        provider=model.provider,
        attestor=model.attestor,
        target_escrow_wei=model.target_escrow_wei,
        escrow_balance_wei=model.escrow_balance_wei,
        job_spec_hash=model.job_spec_hash,
        onchain_status=OnchainJobStatus(model.onchain_status),
        offchain_status=OffchainJobStatus(model.offchain_status),
        attestation_hash=model.attestation_hash,
        settlement_hash=model.settlement_hash,
        provider_payout_wei=model.provider_payout_wei,
        requester_refund_wei=model.requester_refund_wei,
        last_chain_block=model.last_chain_block,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _node_to_entity(model: NodeModel) -> Node:
    return Node(
        node_id=model.node_id,
        role=NodeRole(model.role),
        endpoint_url=model.endpoint_url,
        capabilities=model.capabilities_json,
        status=NodeStatus(model.status),
        last_seen_at=model.last_seen_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _sync_to_entity(model: ChainSyncStateModel) -> ChainSyncState:
    return ChainSyncState(
        sync_key=model.sync_key,
        chain_id=model.chain_id,
        contract_address=model.contract_address,
        last_processed_block=model.last_processed_block,
        updated_at=model.updated_at,
    )


class SqlAlchemyJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, job_id: int) -> Job | None:
        model = self.session.get(JobModel, job_id)
        return _job_to_entity(model) if model else None

    def list(self) -> Sequence[Job]:
        return [_job_to_entity(model) for model in self.session.query(JobModel).order_by(JobModel.job_id).all()]

    def list_by_offchain_status(self, status: OffchainJobStatus) -> Sequence[Job]:
        models = self.session.query(JobModel).filter(JobModel.offchain_status == status.value).order_by(JobModel.job_id).all()
        return [_job_to_entity(model) for model in models]

    def upsert(self, job: Job) -> Job:
        model = self.session.get(JobModel, job.job_id)
        if model is None:
            model = JobModel(job_id=job.job_id)
            self.session.add(model)

        model.requester = job.requester
        model.provider = job.provider
        model.attestor = job.attestor
        model.target_escrow_wei = job.target_escrow_wei
        model.escrow_balance_wei = job.escrow_balance_wei
        model.job_spec_hash = job.job_spec_hash
        model.onchain_status = job.onchain_status.value
        model.offchain_status = job.offchain_status.value
        model.attestation_hash = job.attestation_hash
        model.settlement_hash = job.settlement_hash
        model.provider_payout_wei = job.provider_payout_wei
        model.requester_refund_wei = job.requester_refund_wei
        model.last_chain_block = job.last_chain_block
        self.session.flush()
        return _job_to_entity(model)


class SqlAlchemyNodeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, node_id: str) -> Node | None:
        model = self.session.get(NodeModel, node_id)
        return _node_to_entity(model) if model else None

    def list(self) -> Sequence[Node]:
        return [_node_to_entity(model) for model in self.session.query(NodeModel).order_by(NodeModel.node_id).all()]

    def list_by_role(self, role: NodeRole) -> Sequence[Node]:
        models = self.session.query(NodeModel).filter(NodeModel.role == role.value).order_by(NodeModel.node_id).all()
        return [_node_to_entity(model) for model in models]

    def upsert(self, node: Node) -> Node:
        model = self.session.get(NodeModel, node.node_id)
        if model is None:
            model = NodeModel(node_id=node.node_id)
            self.session.add(model)
            model.created_at = datetime.now(timezone.utc)

        model.role = node.role.value
        model.endpoint_url = node.endpoint_url
        model.capabilities_json = node.capabilities
        model.status = node.status.value
        model.last_seen_at = node.last_seen_at
        self.session.flush()
        return _node_to_entity(model)


class SqlAlchemySyncStateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, sync_key: str) -> ChainSyncState | None:
        model = self.session.get(ChainSyncStateModel, sync_key)
        return _sync_to_entity(model) if model else None

    def upsert(self, state: ChainSyncState) -> ChainSyncState:
        model = self.session.get(ChainSyncStateModel, state.sync_key)
        if model is None:
            model = ChainSyncStateModel(sync_key=state.sync_key)
            self.session.add(model)
        model.chain_id = state.chain_id
        model.contract_address = state.contract_address
        model.last_processed_block = state.last_processed_block
        self.session.flush()
        return _sync_to_entity(model)


class SqlAlchemyJobEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def exists(self, transaction_hash: str, log_index: int) -> bool:
        model = (
            self.session.query(JobEventModel)
            .filter(JobEventModel.transaction_hash == transaction_hash, JobEventModel.log_index == log_index)
            .one_or_none()
        )
        return model is not None

    def add(self, event: JobEventRecord) -> JobEventRecord:
        model = JobEventModel(
            event_name=event.event_name,
            transaction_hash=event.transaction_hash,
            log_index=event.log_index,
            block_number=event.block_number,
            job_id=event.job_id,
            payload_json=event.payload,
        )
        self.session.add(model)
        self.session.flush()
        return event
