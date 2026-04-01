from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from orchestrator.app.application.protocol_runtime.fedavg_like_v1 import FedAvgLikeV1Protocol
from orchestrator.app.application.protocol_runtime.registry import ProtocolRegistry
from orchestrator.app.application.services.fedavg_like_aggregation_service import FedAvgLikeAggregationService
from orchestrator.app.application.services.protocol_run_service import ProtocolRunService
from orchestrator.app.application.services.round_reconciliation_service import RoundReconciliationService
from orchestrator.app.application.services import (
    ArtifactService,
    EvaluationClaimService,
    EvaluationCompletionService,
    EvaluationDispatchService,
    JobSyncService,
    NodeLivenessService,
    NodeRegistryService,
    OrchestrationCoordinator,
    SchedulingPreparationService,
    StatusService,
    TaskClaimService,
    TaskCompletionService,
    TaskDispatchService,
)
from orchestrator.app.infrastructure.container import AppContainer


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_db_session(container: AppContainer = Depends(get_container)) -> Iterator[Session]:
    session = container.session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_node_liveness_service(container: AppContainer = Depends(get_container)) -> NodeLivenessService:
    return NodeLivenessService(container.settings.node_stale_after_seconds)


def get_node_registry_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> NodeRegistryService:
    return NodeRegistryService(repository=container.node_repository(session))


def get_scheduling_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> SchedulingPreparationService:
    return SchedulingPreparationService(
        jobs=container.job_repository(session),
        nodes=container.node_repository(session),
        lifecycle=container.lifecycle_service,
        node_selection=container.node_selection_strategy,
    )


def get_job_sync_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> JobSyncService:
    settings = container.settings
    return JobSyncService(
        blockchain=container.blockchain_client,
        jobs=container.job_repository(session),
        sync_state=container.sync_state_repository(session),
        job_events=container.job_event_repository(session),
        lifecycle=container.lifecycle_service,
        chain_id=settings.chain_id,
        contract_address=settings.marketplace_contract_address,
        start_block=settings.sync_start_block,
        batch_size=settings.sync_batch_size,
    )


def get_artifact_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> ArtifactService:
    return ArtifactService(repository=container.artifact_repository(session), storage=container.artifact_storage)


def get_task_claim_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> TaskClaimService:
    return TaskClaimService(tasks=container.training_task_repository(session), nodes=container.node_repository(session))


def get_task_completion_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> TaskCompletionService:
    return TaskCompletionService(
        tasks=container.training_task_repository(session),
        artifacts=container.artifact_repository(session),
    )


def get_task_dispatch_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
    artifact_service: ArtifactService = Depends(get_artifact_service),
) -> TaskDispatchService:
    return TaskDispatchService(
        jobs=container.job_repository(session),
        nodes=container.node_repository(session),
        tasks=container.training_task_repository(session),
        artifacts=artifact_service,
    )


def get_evaluation_claim_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> EvaluationClaimService:
    return EvaluationClaimService(
        tasks=container.evaluation_task_repository(session),
        nodes=container.node_repository(session),
    )


def get_evaluation_completion_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> EvaluationCompletionService:
    return EvaluationCompletionService(
        tasks=container.evaluation_task_repository(session),
        artifacts=container.artifact_repository(session),
        reports=container.evaluation_report_repository(session),
        jobs=container.job_repository(session),
    )


def get_evaluation_dispatch_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
    artifact_service: ArtifactService = Depends(get_artifact_service),
) -> EvaluationDispatchService:
    return EvaluationDispatchService(
        jobs=container.job_repository(session),
        nodes=container.node_repository(session),
        training_tasks=container.training_task_repository(session),
        evaluation_tasks=container.evaluation_task_repository(session),
        artifacts=artifact_service,
    )


def get_fedavg_like_aggregation_service(
    artifact_service: ArtifactService = Depends(get_artifact_service),
) -> FedAvgLikeAggregationService:
    return FedAvgLikeAggregationService(artifacts=artifact_service)


def get_fedavg_like_protocol(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
    artifact_service: ArtifactService = Depends(get_artifact_service),
    aggregation_service: FedAvgLikeAggregationService = Depends(get_fedavg_like_aggregation_service),
) -> FedAvgLikeV1Protocol:
    return FedAvgLikeV1Protocol(
        jobs=container.job_repository(session),
        nodes=container.node_repository(session),
        rounds=container.round_repository(session),
        training_tasks=container.training_task_repository(session),
        evaluation_tasks=container.evaluation_task_repository(session),
        artifacts=artifact_service,
        aggregation=aggregation_service,
    )


def get_protocol_registry(
    protocol: FedAvgLikeV1Protocol = Depends(get_fedavg_like_protocol),
) -> ProtocolRegistry:
    return ProtocolRegistry([protocol])


def get_protocol_run_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
    protocols: ProtocolRegistry = Depends(get_protocol_registry),
) -> ProtocolRunService:
    return ProtocolRunService(jobs=container.job_repository(session), protocols=protocols)


def get_round_reconciliation_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
    protocols: ProtocolRegistry = Depends(get_protocol_registry),
) -> RoundReconciliationService:
    return RoundReconciliationService(
        rounds=container.round_repository(session),
        jobs=container.job_repository(session),
        training_tasks=container.training_task_repository(session),
        evaluation_tasks=container.evaluation_task_repository(session),
        evaluation_reports=container.evaluation_report_repository(session),
        protocols=protocols,
    )


def get_status_service(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
) -> tuple[StatusService, int | None]:
    sync_state = container.sync_state_repository(session).get(
        f"{container.settings.chain_id}:{container.settings.marketplace_contract_address.lower()}"
    )
    last_processed_block = sync_state.last_processed_block if sync_state else None
    return StatusService(
        settings=container.settings,
        engine=container.engine,
        blockchain=container.blockchain_client,
    ), last_processed_block


def get_orchestration_coordinator(
    sync_service: JobSyncService = Depends(get_job_sync_service),
    scheduling_service: SchedulingPreparationService = Depends(get_scheduling_service),
) -> OrchestrationCoordinator:
    return OrchestrationCoordinator(sync_service=sync_service, scheduling_service=scheduling_service)
