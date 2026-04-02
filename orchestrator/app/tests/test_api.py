from fastapi import HTTPException

from orchestrator.app.api.routes.jobs import get_job, list_jobs, sync_jobs
from orchestrator.app.api.routes.jobs import list_job_evaluation_tasks, list_job_training_tasks
from orchestrator.app.api.routes.nodes import get_node, heartbeat_node, list_nodes, register_node
from orchestrator.app.api.routes.rounds import get_round, list_rounds
from orchestrator.app.application.services.round_reconciliation_service import RoundReconciliationService
from orchestrator.app.domain.entities import EvaluationTask, Job, Round, TrainingTask
from orchestrator.app.domain.enums import EvaluationTaskStatus, OffchainJobStatus, OnchainJobStatus, RoundStatus, TrainingTaskStatus, TrainingTaskType
from orchestrator.app.api.routes.status import status
from orchestrator.app.application.dto import NodeHeartbeatRequest, NodeRegistrationRequest
from orchestrator.app.application.services import (
    JobSyncService,
    NodeLivenessService,
    NodeRegistryService,
    SchedulingPreparationService,
    StatusService,
)
from orchestrator.app.infrastructure.blockchain.types import ChainEvent

from .conftest import build_snapshot


class _UnusedProtocols:
    def get(self, protocol_name: str):  # pragma: no cover - defensive stub for read-only service paths
        raise AssertionError(f"unexpected protocol lookup: {protocol_name}")


def test_status_and_missing_resources(app) -> None:
    container = app.state.container
    session = container.session_factory()
    try:
        sync_state = container.sync_state_repository(session).get(
            f"{container.settings.chain_id}:{container.settings.marketplace_contract_address.lower()}"
        )
        last_processed_block = sync_state.last_processed_block if sync_state else None
        payload = status((StatusService(settings=container.settings, engine=container.engine, blockchain=container.blockchain_client), last_processed_block))
        assert payload.status == "ok"
        assert payload.configured_chain_id == 31337

        try:
            get_job(999, session, container)
        except HTTPException as exc:
            assert exc.status_code == 404
            assert exc.detail == "job not found"
        else:
            raise AssertionError("expected HTTPException for missing job")
    finally:
        session.close()


def test_node_registration_and_heartbeat_flow(app) -> None:
    container = app.state.container
    session = container.session_factory()
    try:
        registry = NodeRegistryService(container.node_repository(session))
        liveness = NodeLivenessService(container.settings.node_stale_after_seconds)

        created = register_node(
            NodeRegistrationRequest(
                node_id="trainer-1",
                role="trainer",
                endpoint_url="http://trainer.local/callback",
                capabilities={"gpu": False},
            ),
            registry,
        )
        assert created.status == "registered"

        heartbeat = heartbeat_node(NodeHeartbeatRequest(node_id="trainer-1"), registry)
        assert heartbeat.status == "online"

        listed = list_nodes(session, container, liveness)
        assert listed[0].node_id == "trainer-1"

        fetched = get_node("trainer-1", session, container, liveness)
        assert fetched.status in {"online", "registered"}
    finally:
        session.close()


def test_sync_and_reconcile_flow(app, fake_blockchain) -> None:
    snapshot = build_snapshot()
    fake_blockchain.add_job(snapshot)
    fake_blockchain.add_event(
        ChainEvent(
            event_name="JobCreated",
            block_number=1,
            transaction_hash="0x100",
            log_index=0,
            args={
                "jobId": 1,
                "requester": snapshot.requester,
                "provider": snapshot.provider,
                "attestor": snapshot.attestor,
                "targetEscrow": snapshot.target_escrow_wei,
                "jobSpecHash": snapshot.job_spec_hash,
            },
        )
    )
    fake_blockchain.add_event(
        ChainEvent(
            event_name="JobFullyFunded",
            block_number=2,
            transaction_hash="0x101",
            log_index=0,
            args={"jobId": 1, "escrowBalance": 10},
        )
    )

    container = app.state.container
    session = container.session_factory()
    try:
        sync_service = JobSyncService(
            blockchain=container.blockchain_client,
            jobs=container.job_repository(session),
            sync_state=container.sync_state_repository(session),
            job_events=container.job_event_repository(session),
            lifecycle=container.lifecycle_service,
            chain_id=container.settings.chain_id,
            contract_address=container.settings.marketplace_contract_address,
            start_block=container.settings.sync_start_block,
            batch_size=container.settings.sync_batch_size,
        )
        sync_result = sync_jobs(sync_service)
        assert sync_result.processed_events == 2

        jobs = list_jobs(session, container)
        assert jobs[0].offchain_status == "funded"

        registry = NodeRegistryService(container.node_repository(session))
        register_node(
            NodeRegistrationRequest(
                node_id="trainer-1",
                role="trainer",
                endpoint_url="http://trainer.local/callback",
                capabilities=None,
            ),
            registry,
        )
        heartbeat_node(NodeHeartbeatRequest(node_id="trainer-1"), registry)
        register_node(
            NodeRegistrationRequest(
                node_id="evaluator-1",
                role="evaluator",
                endpoint_url="http://evaluator.local/callback",
                capabilities=None,
            ),
            registry,
        )
        heartbeat_node(NodeHeartbeatRequest(node_id="evaluator-1"), registry)

        scheduler = SchedulingPreparationService(
            jobs=container.job_repository(session),
            nodes=container.node_repository(session),
            lifecycle=container.lifecycle_service,
            node_selection=container.node_selection_strategy,
        )
        assert scheduler.reconcile() == 1
        assert get_job(1, session, container).offchain_status == "ready_for_scheduling"
        assert scheduler.reconcile() == 1
        assert get_job(1, session, container).offchain_status == "scheduling"
    finally:
        session.close()


def test_round_and_task_listing_routes(app) -> None:
    container = app.state.container
    session = container.session_factory()
    try:
        container.job_repository(session).upsert(
            Job(
                job_id=7,
                requester="0x00000000000000000000000000000000000000a1",
                provider="0x00000000000000000000000000000000000000b2",
                attestor="0x00000000000000000000000000000000000000c3",
                target_escrow_wei=10,
                escrow_balance_wei=10,
                job_spec_hash="0x" + "7" * 64,
                onchain_status=OnchainJobStatus.FUNDED,
                offchain_status=OffchainJobStatus.SCHEDULING,
            )
        )
        container.round_repository(session).upsert(
            Round(
                round_id="round-7",
                job_id=7,
                protocol_name="fedavg_like_v1",
                round_index=1,
                status=RoundStatus.TRAINING,
                base_model_artifact_uri="artifact://base-7",
            )
        )
        container.training_task_repository(session).upsert(
            TrainingTask(
                task_id="task-7",
                job_id=7,
                round_id="round-7",
                trainer_node_id="trainer-1",
                task_type=TrainingTaskType.LOCAL_FIT,
                status=TrainingTaskStatus.RUNNING,
                data_partition_id="partition-1",
                model_artifact_uri="artifact://base-7",
                dataset_artifact_uri="artifact://dataset-7",
                config_json={"epochs": 1},
            )
        )
        container.evaluation_task_repository(session).upsert(
            EvaluationTask(
                evaluation_task_id="evaluation-task-7",
                job_id=7,
                round_id="round-7",
                source_training_task_id=None,
                evaluator_node_id=None,
                status=EvaluationTaskStatus.PENDING,
                target_model_artifact_uri="artifact://aggregated-7",
                dataset_artifact_uri="artifact://evaluation-7",
                config_json={"accuracy_threshold": 0.75},
            )
        )

        round_service = RoundReconciliationService(
            rounds=container.round_repository(session),
            jobs=container.job_repository(session),
            training_tasks=container.training_task_repository(session),
            evaluation_tasks=container.evaluation_task_repository(session),
            evaluation_reports=container.evaluation_report_repository(session),
            protocols=_UnusedProtocols(),
        )

        rounds = list_rounds(round_service, None)
        assert rounds[0].round_id == "round-7"

        filtered_rounds = list_rounds(round_service, 7)
        assert filtered_rounds[0].job_id == 7

        fetched_round = get_round("round-7", round_service)
        assert fetched_round.status == "training"

        training_tasks = list_job_training_tasks(7, session, container)
        assert training_tasks[0].task_id == "task-7"

        evaluation_tasks = list_job_evaluation_tasks(7, session, container)
        assert evaluation_tasks[0].evaluation_task_id == "evaluation-task-7"
    finally:
        session.close()
