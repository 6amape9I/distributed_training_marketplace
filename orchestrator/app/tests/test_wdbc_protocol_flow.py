from __future__ import annotations

import json

from orchestrator.app.api.routes.internal import start_protocol_run_for_job
from orchestrator.app.application.protocol_runtime import FedAvgLikeV1Protocol, FedAvgLikeWdbcV1Protocol, ProtocolRegistry
from orchestrator.app.application.services import (
    ArtifactService,
    EvaluationClaimService,
    EvaluationCompletionService,
    NodeRegistryService,
    TaskClaimService,
    TaskCompletionService,
)
from orchestrator.app.application.services.fedavg_like_aggregation_service import FedAvgLikeAggregationService
from orchestrator.app.application.services.protocol_run_service import ProtocolRunService
from orchestrator.app.application.services.round_reconciliation_service import RoundReconciliationService
from orchestrator.app.domain.entities import Job
from orchestrator.app.domain.enums import ArtifactKind, NodeRole, OffchainJobStatus, OnchainJobStatus, RoundStatus
from evaluator_agent.app.execution import EvaluationExecutor
from shared.python.experiments import ensure_prepared_wdbc_dataset
from shared.python.schemas import EvaluationTaskRecord, TrainingTaskRecord
from trainer_agent.app.execution import LocalFitExecutor


def _training_record(task) -> TrainingTaskRecord:
    return TrainingTaskRecord(
        task_id=task.task_id,
        job_id=task.job_id,
        round_id=task.round_id,
        trainer_node_id=task.trainer_node_id,
        task_type=task.task_type.value,
        status=task.status.value,
        data_partition_id=task.data_partition_id,
        model_artifact_uri=task.model_artifact_uri,
        dataset_artifact_uri=task.dataset_artifact_uri,
        config_json=task.config_json,
        result_artifact_uri=task.result_artifact_uri,
        result_artifact_hash=task.result_artifact_hash,
        report_artifact_uri=task.report_artifact_uri,
        report_artifact_hash=task.report_artifact_hash,
        claimed_at=task.claimed_at,
        completed_at=task.completed_at,
        failure_reason=task.failure_reason,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _evaluation_record(task) -> EvaluationTaskRecord:
    return EvaluationTaskRecord(
        evaluation_task_id=task.evaluation_task_id,
        job_id=task.job_id,
        round_id=task.round_id,
        source_training_task_id=task.source_training_task_id,
        evaluator_node_id=task.evaluator_node_id,
        status=task.status.value,
        target_model_artifact_uri=task.target_model_artifact_uri,
        dataset_artifact_uri=task.dataset_artifact_uri,
        config_json=task.config_json,
        report_artifact_uri=task.report_artifact_uri,
        report_artifact_hash=task.report_artifact_hash,
        claimed_at=task.claimed_at,
        completed_at=task.completed_at,
        failure_reason=task.failure_reason,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _artifact_service(container, session) -> ArtifactService:
    return ArtifactService(container.artifact_repository(session), container.artifact_storage)


def _register_online_nodes(container, session) -> None:
    registry = NodeRegistryService(container.node_repository(session))
    for node_id in ("trainer-1", "trainer-2"):
        registry.register(node_id=node_id, role=NodeRole.TRAINER, endpoint_url=f"http://{node_id}.local", capabilities={"cpu": True})
        registry.heartbeat(node_id)
    registry.register(node_id="evaluator-1", role=NodeRole.EVALUATOR, endpoint_url="http://evaluator-1.local", capabilities={"metrics": ["accuracy"]})
    registry.heartbeat("evaluator-1")


def test_wdbc_protocol_run_uses_prepared_dataset_and_reaches_ready_for_attestation(app) -> None:
    ensure_prepared_wdbc_dataset()

    container = app.state.container
    session = container.session_factory()
    try:
        container.job_repository(session).upsert(
            Job(
                job_id=301,
                requester="0x00000000000000000000000000000000000000a1",
                provider="0x00000000000000000000000000000000000000b2",
                attestor="0x00000000000000000000000000000000000000c3",
                target_escrow_wei=10,
                escrow_balance_wei=10,
                job_spec_hash="0x" + "3" * 64,
                onchain_status=OnchainJobStatus.FUNDED,
                offchain_status=OffchainJobStatus.SCHEDULING,
            )
        )
        _register_online_nodes(container, session)

        artifact_service = _artifact_service(container, session)
        aggregation_service = FedAvgLikeAggregationService(artifact_service)
        registry = ProtocolRegistry(
            [
                FedAvgLikeV1Protocol(
                    jobs=container.job_repository(session),
                    nodes=container.node_repository(session),
                    rounds=container.round_repository(session),
                    training_tasks=container.training_task_repository(session),
                    evaluation_tasks=container.evaluation_task_repository(session),
                    artifacts=artifact_service,
                    aggregation=aggregation_service,
                ),
                FedAvgLikeWdbcV1Protocol(
                    jobs=container.job_repository(session),
                    nodes=container.node_repository(session),
                    rounds=container.round_repository(session),
                    training_tasks=container.training_task_repository(session),
                    evaluation_tasks=container.evaluation_task_repository(session),
                    artifacts=artifact_service,
                    aggregation=aggregation_service,
                ),
            ]
        )
        run_service = ProtocolRunService(jobs=container.job_repository(session), protocols=registry)
        response = start_protocol_run_for_job(301, run_service, "fedavg_like_wdbc_v1", session)
        assert response.protocol_name == "fedavg_like_wdbc_v1"

        tasks = list(container.training_task_repository(session).list_by_job(301))
        assert len(tasks) == 2
        first_manifest = json.loads(
            artifact_service.read_content(tasks[0].dataset_artifact_uri.split("artifact://", 1)[1]).decode("utf-8")
        )
        assert first_manifest["feature_count"] == 30
        assert len(first_manifest["feature_scales"]) == 30
        assert first_manifest["dataset_name"] == "wdbc"

        claim_service = TaskClaimService(container.training_task_repository(session), container.node_repository(session))
        completion_service = TaskCompletionService(container.training_task_repository(session), container.artifact_repository(session))
        fit_executor = LocalFitExecutor()
        for trainer_id in ("trainer-1", "trainer-2"):
            claimed = claim_service.claim_next(trainer_id)
            assert claimed is not None
            model_payload = artifact_service.read_content(claimed.model_artifact_uri.split("artifact://", 1)[1])
            dataset_payload = artifact_service.read_content(claimed.dataset_artifact_uri.split("artifact://", 1)[1])
            execution = fit_executor.execute(
                task=_training_record(claimed),
                trainer_node_id=trainer_id,
                model_payload=model_payload,
                dataset_payload=dataset_payload,
            )
            result_artifact = artifact_service.upload(
                kind=ArtifactKind.TASK_RESULT,
                name=f"{claimed.task_id}-result.json",
                payload=execution.result_payload,
                mime_type="application/json",
                metadata={"round_id": claimed.round_id},
                job_id=claimed.job_id,
                task_id=claimed.task_id,
            )
            report_artifact = artifact_service.upload(
                kind=ArtifactKind.TRAINER_REPORT,
                name=f"{claimed.task_id}-report.json",
                payload=execution.report_payload,
                mime_type="application/json",
                metadata={"round_id": claimed.round_id},
                job_id=claimed.job_id,
                task_id=claimed.task_id,
            )
            completion_service.complete(claimed.task_id, trainer_id, result_artifact.artifact_id, report_artifact.artifact_id)

        round_id = response.round_id
        reconcile_service = RoundReconciliationService(
            rounds=container.round_repository(session),
            jobs=container.job_repository(session),
            training_tasks=container.training_task_repository(session),
            evaluation_tasks=container.evaluation_task_repository(session),
            evaluation_reports=container.evaluation_report_repository(session),
            protocols=registry,
        )
        aggregated_round = reconcile_service.reconcile(round_id)
        assert aggregated_round.status == RoundStatus.EVALUATING

        evaluation_tasks = list(container.evaluation_task_repository(session).list_by_round(round_id))
        assert len(evaluation_tasks) == 1

        eval_claim_service = EvaluationClaimService(container.evaluation_task_repository(session), container.node_repository(session))
        eval_completion_service = EvaluationCompletionService(
            tasks=container.evaluation_task_repository(session),
            artifacts=container.artifact_repository(session),
            reports=container.evaluation_report_repository(session),
            jobs=container.job_repository(session),
        )
        claimed_eval = eval_claim_service.claim_next("evaluator-1")
        assert claimed_eval is not None
        aggregated_payload = artifact_service.read_content(claimed_eval.target_model_artifact_uri.split("artifact://", 1)[1])
        eval_dataset_payload = artifact_service.read_content(claimed_eval.dataset_artifact_uri.split("artifact://", 1)[1])
        eval_artifacts = EvaluationExecutor().execute(
            task=_evaluation_record(claimed_eval),
            model_payload=aggregated_payload,
            dataset_payload=eval_dataset_payload,
        )
        report_artifact = artifact_service.upload(
            kind=ArtifactKind.EVALUATION_REPORT,
            name=f"{claimed_eval.evaluation_task_id}-report.json",
            payload=eval_artifacts.report_payload,
            mime_type="application/json",
            metadata={"round_id": round_id},
            job_id=claimed_eval.job_id,
            task_id=claimed_eval.evaluation_task_id,
        )
        eval_completion_service.complete(
            claimed_eval.evaluation_task_id,
            "evaluator-1",
            report_artifact.artifact_id,
            eval_artifacts.metrics_json,
            eval_artifacts.sample_count,
            eval_artifacts.acceptance_decision,
            eval_artifacts.target_model_digest,
        )

        final_round = reconcile_service.reconcile(round_id)
        assert final_round.status == RoundStatus.COMPLETED
        assert container.job_repository(session).get(301).offchain_status == OffchainJobStatus.READY_FOR_ATTESTATION
    finally:
        session.close()
