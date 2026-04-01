from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from orchestrator.app.domain.entities import (
    Artifact,
    ChainSyncState,
    EvaluationReport,
    EvaluationTask,
    Job,
    JobEventRecord,
    Node,
    Round,
    TrainingTask,
)
from orchestrator.app.domain.enums import (
    ArtifactKind,
    EvaluationTaskStatus,
    NodeRole,
    NodeStatus,
    OffchainJobStatus,
    OnchainJobStatus,
    RoundStatus,
    TrainingTaskStatus,
    TrainingTaskType,
)
from orchestrator.app.infrastructure.db.models import (
    ArtifactModel,
    ChainSyncStateModel,
    EvaluationReportModel,
    EvaluationTaskModel,
    JobEventModel,
    JobModel,
    NodeModel,
    RoundModel,
    TrainingTaskModel,
)


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


def _task_to_entity(model: TrainingTaskModel) -> TrainingTask:
    return TrainingTask(
        task_id=model.task_id,
        job_id=model.job_id,
        round_id=model.round_id,
        trainer_node_id=model.trainer_node_id,
        task_type=TrainingTaskType(model.task_type),
        status=TrainingTaskStatus(model.status),
        data_partition_id=model.data_partition_id,
        model_artifact_uri=model.model_artifact_uri,
        dataset_artifact_uri=model.dataset_artifact_uri,
        config_json=model.config_json,
        result_artifact_uri=model.result_artifact_uri,
        result_artifact_hash=model.result_artifact_hash,
        report_artifact_uri=model.report_artifact_uri,
        report_artifact_hash=model.report_artifact_hash,
        claimed_at=model.claimed_at,
        completed_at=model.completed_at,
        failure_reason=model.failure_reason,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _artifact_to_entity(model: ArtifactModel) -> Artifact:
    return Artifact(
        artifact_id=model.artifact_id,
        kind=ArtifactKind(model.kind),
        uri=model.uri,
        content_hash=model.content_hash,
        content_size_bytes=model.content_size_bytes,
        mime_type=model.mime_type,
        metadata_json=model.metadata_json,
        job_id=model.job_id,
        task_id=model.task_id,
        created_at=model.created_at,
    )


def _evaluation_task_to_entity(model: EvaluationTaskModel) -> EvaluationTask:
    return EvaluationTask(
        evaluation_task_id=model.evaluation_task_id,
        job_id=model.job_id,
        round_id=model.round_id,
        source_training_task_id=model.source_training_task_id,
        evaluator_node_id=model.evaluator_node_id,
        status=EvaluationTaskStatus(model.status),
        target_model_artifact_uri=model.target_model_artifact_uri,
        dataset_artifact_uri=model.dataset_artifact_uri,
        config_json=model.config_json,
        report_artifact_uri=model.report_artifact_uri,
        report_artifact_hash=model.report_artifact_hash,
        claimed_at=model.claimed_at,
        completed_at=model.completed_at,
        failure_reason=model.failure_reason,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _evaluation_report_to_entity(model: EvaluationReportModel) -> EvaluationReport:
    return EvaluationReport(
        report_id=model.report_id,
        evaluation_task_id=model.evaluation_task_id,
        job_id=model.job_id,
        round_id=model.round_id,
        source_training_task_id=model.source_training_task_id,
        evaluator_node_id=model.evaluator_node_id,
        metrics_json=model.metrics_json,
        sample_count=model.sample_count,
        acceptance_decision=model.acceptance_decision,
        target_model_digest=model.target_model_digest,
        created_at=model.created_at,
    )


def _round_to_entity(model: RoundModel) -> Round:
    return Round(
        round_id=model.round_id,
        job_id=model.job_id,
        protocol_name=model.protocol_name,
        round_index=model.round_index,
        status=RoundStatus(model.status),
        base_model_artifact_uri=model.base_model_artifact_uri,
        aggregated_model_artifact_uri=model.aggregated_model_artifact_uri,
        aggregated_model_artifact_hash=model.aggregated_model_artifact_hash,
        evaluation_report_id=model.evaluation_report_id,
        failure_reason=model.failure_reason,
        created_at=model.created_at,
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


class SqlAlchemyTrainingTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, task_id: str) -> TrainingTask | None:
        model = self.session.get(TrainingTaskModel, task_id)
        return _task_to_entity(model) if model else None

    def list(self) -> Sequence[TrainingTask]:
        models = self.session.query(TrainingTaskModel).order_by(TrainingTaskModel.created_at, TrainingTaskModel.task_id).all()
        return [_task_to_entity(model) for model in models]

    def list_by_job(self, job_id: int) -> Sequence[TrainingTask]:
        models = self.session.query(TrainingTaskModel).filter(TrainingTaskModel.job_id == job_id).order_by(TrainingTaskModel.created_at, TrainingTaskModel.task_id).all()
        return [_task_to_entity(model) for model in models]

    def list_by_round(self, round_id: str) -> Sequence[TrainingTask]:
        models = self.session.query(TrainingTaskModel).filter(TrainingTaskModel.round_id == round_id).order_by(TrainingTaskModel.created_at, TrainingTaskModel.task_id).all()
        return [_task_to_entity(model) for model in models]

    def list_by_status(self, status: TrainingTaskStatus) -> Sequence[TrainingTask]:
        models = self.session.query(TrainingTaskModel).filter(TrainingTaskModel.status == status.value).order_by(TrainingTaskModel.created_at, TrainingTaskModel.task_id).all()
        return [_task_to_entity(model) for model in models]

    def list_by_trainer(self, trainer_node_id: str) -> Sequence[TrainingTask]:
        models = self.session.query(TrainingTaskModel).filter(TrainingTaskModel.trainer_node_id == trainer_node_id).order_by(TrainingTaskModel.created_at, TrainingTaskModel.task_id).all()
        return [_task_to_entity(model) for model in models]

    def upsert(self, task: TrainingTask) -> TrainingTask:
        model = self.session.get(TrainingTaskModel, task.task_id)
        if model is None:
            model = TrainingTaskModel(task_id=task.task_id)
            self.session.add(model)
        model.job_id = task.job_id
        model.round_id = task.round_id
        model.trainer_node_id = task.trainer_node_id
        model.task_type = task.task_type.value
        model.status = task.status.value
        model.data_partition_id = task.data_partition_id
        model.model_artifact_uri = task.model_artifact_uri
        model.dataset_artifact_uri = task.dataset_artifact_uri
        model.config_json = task.config_json
        model.result_artifact_uri = task.result_artifact_uri
        model.result_artifact_hash = task.result_artifact_hash
        model.report_artifact_uri = task.report_artifact_uri
        model.report_artifact_hash = task.report_artifact_hash
        model.claimed_at = task.claimed_at
        model.completed_at = task.completed_at
        model.failure_reason = task.failure_reason
        self.session.flush()
        return _task_to_entity(model)

    def claim_next_pending(self, trainer_node_id: str) -> TrainingTask | None:
        while True:
            candidate = (
                self.session.query(TrainingTaskModel)
                .filter(TrainingTaskModel.status == TrainingTaskStatus.PENDING.value)
                .order_by(TrainingTaskModel.created_at, TrainingTaskModel.task_id)
                .first()
            )
            if candidate is None:
                return None
            now = datetime.now(timezone.utc)
            updated = (
                self.session.query(TrainingTaskModel)
                .filter(
                    TrainingTaskModel.task_id == candidate.task_id,
                    TrainingTaskModel.status == TrainingTaskStatus.PENDING.value,
                )
                .update(
                    {
                        TrainingTaskModel.status: TrainingTaskStatus.CLAIMED.value,
                        TrainingTaskModel.trainer_node_id: trainer_node_id,
                        TrainingTaskModel.claimed_at: now,
                    },
                    synchronize_session=False,
                )
            )
            self.session.flush()
            if updated == 1:
                claimed = self.session.get(TrainingTaskModel, candidate.task_id)
                return _task_to_entity(claimed)
            self.session.expire_all()


class SqlAlchemyEvaluationTaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, evaluation_task_id: str) -> EvaluationTask | None:
        model = self.session.get(EvaluationTaskModel, evaluation_task_id)
        return _evaluation_task_to_entity(model) if model else None

    def list(self) -> Sequence[EvaluationTask]:
        models = self.session.query(EvaluationTaskModel).order_by(EvaluationTaskModel.created_at, EvaluationTaskModel.evaluation_task_id).all()
        return [_evaluation_task_to_entity(model) for model in models]

    def list_by_job(self, job_id: int) -> Sequence[EvaluationTask]:
        models = self.session.query(EvaluationTaskModel).filter(EvaluationTaskModel.job_id == job_id).order_by(EvaluationTaskModel.created_at, EvaluationTaskModel.evaluation_task_id).all()
        return [_evaluation_task_to_entity(model) for model in models]

    def list_by_round(self, round_id: str) -> Sequence[EvaluationTask]:
        models = self.session.query(EvaluationTaskModel).filter(EvaluationTaskModel.round_id == round_id).order_by(EvaluationTaskModel.created_at, EvaluationTaskModel.evaluation_task_id).all()
        return [_evaluation_task_to_entity(model) for model in models]

    def list_by_status(self, status: EvaluationTaskStatus) -> Sequence[EvaluationTask]:
        models = self.session.query(EvaluationTaskModel).filter(EvaluationTaskModel.status == status.value).order_by(EvaluationTaskModel.created_at, EvaluationTaskModel.evaluation_task_id).all()
        return [_evaluation_task_to_entity(model) for model in models]

    def list_by_evaluator(self, evaluator_node_id: str) -> Sequence[EvaluationTask]:
        models = self.session.query(EvaluationTaskModel).filter(EvaluationTaskModel.evaluator_node_id == evaluator_node_id).order_by(EvaluationTaskModel.created_at, EvaluationTaskModel.evaluation_task_id).all()
        return [_evaluation_task_to_entity(model) for model in models]

    def upsert(self, task: EvaluationTask) -> EvaluationTask:
        model = self.session.get(EvaluationTaskModel, task.evaluation_task_id)
        if model is None:
            model = EvaluationTaskModel(evaluation_task_id=task.evaluation_task_id)
            self.session.add(model)
        model.job_id = task.job_id
        model.round_id = task.round_id
        model.source_training_task_id = task.source_training_task_id
        model.evaluator_node_id = task.evaluator_node_id
        model.status = task.status.value
        model.target_model_artifact_uri = task.target_model_artifact_uri
        model.dataset_artifact_uri = task.dataset_artifact_uri
        model.config_json = task.config_json
        model.report_artifact_uri = task.report_artifact_uri
        model.report_artifact_hash = task.report_artifact_hash
        model.claimed_at = task.claimed_at
        model.completed_at = task.completed_at
        model.failure_reason = task.failure_reason
        self.session.flush()
        return _evaluation_task_to_entity(model)

    def claim_next_pending(self, evaluator_node_id: str) -> EvaluationTask | None:
        while True:
            candidate = (
                self.session.query(EvaluationTaskModel)
                .filter(EvaluationTaskModel.status == EvaluationTaskStatus.PENDING.value)
                .order_by(EvaluationTaskModel.created_at, EvaluationTaskModel.evaluation_task_id)
                .first()
            )
            if candidate is None:
                return None
            now = datetime.now(timezone.utc)
            updated = (
                self.session.query(EvaluationTaskModel)
                .filter(
                    EvaluationTaskModel.evaluation_task_id == candidate.evaluation_task_id,
                    EvaluationTaskModel.status == EvaluationTaskStatus.PENDING.value,
                )
                .update(
                    {
                        EvaluationTaskModel.status: EvaluationTaskStatus.CLAIMED.value,
                        EvaluationTaskModel.evaluator_node_id: evaluator_node_id,
                        EvaluationTaskModel.claimed_at: now,
                    },
                    synchronize_session=False,
                )
            )
            self.session.flush()
            if updated == 1:
                claimed = self.session.get(EvaluationTaskModel, candidate.evaluation_task_id)
                return _evaluation_task_to_entity(claimed)
            self.session.expire_all()


class SqlAlchemyArtifactRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, artifact_id: str) -> Artifact | None:
        model = self.session.get(ArtifactModel, artifact_id)
        return _artifact_to_entity(model) if model else None

    def list(self) -> Sequence[Artifact]:
        models = self.session.query(ArtifactModel).order_by(ArtifactModel.created_at, ArtifactModel.artifact_id).all()
        return [_artifact_to_entity(model) for model in models]

    def list_by_task(self, task_id: str) -> Sequence[Artifact]:
        models = self.session.query(ArtifactModel).filter(ArtifactModel.task_id == task_id).order_by(ArtifactModel.created_at, ArtifactModel.artifact_id).all()
        return [_artifact_to_entity(model) for model in models]

    def upsert(self, artifact: Artifact) -> Artifact:
        model = self.session.get(ArtifactModel, artifact.artifact_id)
        if model is None:
            model = ArtifactModel(artifact_id=artifact.artifact_id)
            self.session.add(model)
        model.kind = artifact.kind.value
        model.uri = artifact.uri
        model.content_hash = artifact.content_hash
        model.content_size_bytes = artifact.content_size_bytes
        model.mime_type = artifact.mime_type
        model.metadata_json = artifact.metadata_json
        model.job_id = artifact.job_id
        model.task_id = artifact.task_id
        self.session.flush()
        return _artifact_to_entity(model)


class SqlAlchemyEvaluationReportRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, report_id: str) -> EvaluationReport | None:
        model = self.session.get(EvaluationReportModel, report_id)
        return _evaluation_report_to_entity(model) if model else None

    def list(self) -> Sequence[EvaluationReport]:
        models = self.session.query(EvaluationReportModel).order_by(EvaluationReportModel.created_at, EvaluationReportModel.report_id).all()
        return [_evaluation_report_to_entity(model) for model in models]

    def list_by_job(self, job_id: int) -> Sequence[EvaluationReport]:
        models = self.session.query(EvaluationReportModel).filter(EvaluationReportModel.job_id == job_id).order_by(EvaluationReportModel.created_at, EvaluationReportModel.report_id).all()
        return [_evaluation_report_to_entity(model) for model in models]

    def list_by_round(self, round_id: str) -> Sequence[EvaluationReport]:
        models = self.session.query(EvaluationReportModel).filter(EvaluationReportModel.round_id == round_id).order_by(EvaluationReportModel.created_at, EvaluationReportModel.report_id).all()
        return [_evaluation_report_to_entity(model) for model in models]

    def list_by_evaluation_task(self, evaluation_task_id: str) -> Sequence[EvaluationReport]:
        models = self.session.query(EvaluationReportModel).filter(EvaluationReportModel.evaluation_task_id == evaluation_task_id).order_by(EvaluationReportModel.created_at, EvaluationReportModel.report_id).all()
        return [_evaluation_report_to_entity(model) for model in models]

    def upsert(self, report: EvaluationReport) -> EvaluationReport:
        model = self.session.get(EvaluationReportModel, report.report_id)
        if model is None:
            model = EvaluationReportModel(report_id=report.report_id)
            self.session.add(model)
        model.evaluation_task_id = report.evaluation_task_id
        model.job_id = report.job_id
        model.round_id = report.round_id
        model.source_training_task_id = report.source_training_task_id
        model.evaluator_node_id = report.evaluator_node_id
        model.metrics_json = report.metrics_json
        model.sample_count = report.sample_count
        model.acceptance_decision = report.acceptance_decision
        model.target_model_digest = report.target_model_digest
        self.session.flush()
        return _evaluation_report_to_entity(model)


class SqlAlchemyRoundRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, round_id: str) -> Round | None:
        model = self.session.get(RoundModel, round_id)
        return _round_to_entity(model) if model else None

    def list(self) -> Sequence[Round]:
        models = self.session.query(RoundModel).order_by(RoundModel.created_at, RoundModel.round_id).all()
        return [_round_to_entity(model) for model in models]

    def list_by_job(self, job_id: int) -> Sequence[Round]:
        models = self.session.query(RoundModel).filter(RoundModel.job_id == job_id).order_by(RoundModel.round_index, RoundModel.round_id).all()
        return [_round_to_entity(model) for model in models]

    def list_by_status(self, status: RoundStatus) -> Sequence[Round]:
        models = self.session.query(RoundModel).filter(RoundModel.status == status.value).order_by(RoundModel.created_at, RoundModel.round_id).all()
        return [_round_to_entity(model) for model in models]

    def get_active_for_job(self, job_id: int) -> Round | None:
        active_statuses = {
            RoundStatus.PENDING.value,
            RoundStatus.SEEDED.value,
            RoundStatus.TRAINING.value,
            RoundStatus.AGGREGATING.value,
            RoundStatus.EVALUATING.value,
        }
        model = (
            self.session.query(RoundModel)
            .filter(RoundModel.job_id == job_id, RoundModel.status.in_(active_statuses))
            .order_by(RoundModel.round_index.desc(), RoundModel.round_id.desc())
            .first()
        )
        return _round_to_entity(model) if model else None

    def upsert(self, round_record: Round) -> Round:
        model = self.session.get(RoundModel, round_record.round_id)
        if model is None:
            model = RoundModel(round_id=round_record.round_id)
            self.session.add(model)
        model.job_id = round_record.job_id
        model.protocol_name = round_record.protocol_name
        model.round_index = round_record.round_index
        model.status = round_record.status.value
        model.base_model_artifact_uri = round_record.base_model_artifact_uri
        model.aggregated_model_artifact_uri = round_record.aggregated_model_artifact_uri
        model.aggregated_model_artifact_hash = round_record.aggregated_model_artifact_hash
        model.evaluation_report_id = round_record.evaluation_report_id
        model.failure_reason = round_record.failure_reason
        self.session.flush()
        return _round_to_entity(model)
