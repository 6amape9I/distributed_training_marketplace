from __future__ import annotations

import json
from math import isclose

from orchestrator.app.application.protocol_runtime.fedavg_like_v1 import FedAvgLikeV1Protocol
from orchestrator.app.application.protocol_runtime.registry import ProtocolRegistry
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
from shared.python.schemas import EvaluationTaskRecord, TrainingTaskRecord
from trainer_agent.app.execution import LocalFitExecutor
from evaluator_agent.app.execution import EvaluationExecutor


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


def test_protocol_run_aggregates_trainer_outputs_and_reaches_ready_for_attestation(app) -> None:
    container = app.state.container
    session = container.session_factory()
    try:
        container.job_repository(session).upsert(
            Job(
                job_id=101,
                requester="0x00000000000000000000000000000000000000a1",
                provider="0x00000000000000000000000000000000000000b2",
                attestor="0x00000000000000000000000000000000000000c3",
                target_escrow_wei=10,
                escrow_balance_wei=10,
                job_spec_hash="0x" + "1" * 64,
                onchain_status=OnchainJobStatus.FUNDED,
                offchain_status=OffchainJobStatus.SCHEDULING,
            )
        )
        _register_online_nodes(container, session)

        artifact_service = _artifact_service(container, session)
        protocol = FedAvgLikeV1Protocol(
            jobs=container.job_repository(session),
            nodes=container.node_repository(session),
            rounds=container.round_repository(session),
            training_tasks=container.training_task_repository(session),
            evaluation_tasks=container.evaluation_task_repository(session),
            artifacts=artifact_service,
            aggregation=FedAvgLikeAggregationService(artifact_service),
        )
        registry = ProtocolRegistry([protocol])
        run_service = ProtocolRunService(jobs=container.job_repository(session), protocols=registry)
        result = run_service.start_for_job(101)
        round_id = result.round_record.round_id
        assert result.round_record.status == RoundStatus.TRAINING
        assert len(result.training_tasks) == 2

        claim_service = TaskClaimService(container.training_task_repository(session), container.node_repository(session))
        completion_service = TaskCompletionService(container.training_task_repository(session), container.artifact_repository(session))
        fit_executor = LocalFitExecutor()
        claimed_one = claim_service.claim_next("trainer-1")
        claimed_two = claim_service.claim_next("trainer-2")
        assert claimed_one is not None and claimed_two is not None
        assert claimed_one.round_id == round_id and claimed_two.round_id == round_id

        trainer_results: dict[str, dict[str, object]] = {}
        for claimed, trainer_id in ((claimed_one, "trainer-1"), (claimed_two, "trainer-2")):
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
                metadata={"round_id": round_id},
                job_id=claimed.job_id,
                task_id=claimed.task_id,
            )
            report_artifact = artifact_service.upload(
                kind=ArtifactKind.TRAINER_REPORT,
                name=f"{claimed.task_id}-report.json",
                payload=execution.report_payload,
                mime_type="application/json",
                metadata={"round_id": round_id},
                job_id=claimed.job_id,
                task_id=claimed.task_id,
            )
            completion_service.complete(claimed.task_id, trainer_id, result_artifact.artifact_id, report_artifact.artifact_id)
            trainer_results[claimed.task_id] = json.loads(execution.result_payload.decode("utf-8"))

        reconcile_service = RoundReconciliationService(
            rounds=container.round_repository(session),
            jobs=container.job_repository(session),
            training_tasks=container.training_task_repository(session),
            evaluation_tasks=container.evaluation_task_repository(session),
            evaluation_reports=container.evaluation_report_repository(session),
            protocols=registry,
        )
        round_after_aggregation = reconcile_service.reconcile(round_id)
        assert round_after_aggregation.status == RoundStatus.EVALUATING
        assert round_after_aggregation.aggregated_model_artifact_uri is not None

        aggregated_payload = artifact_service.read_content(round_after_aggregation.aggregated_model_artifact_uri.split("artifact://", 1)[1])
        aggregated_model = json.loads(aggregated_payload.decode("utf-8"))
        total_samples = sum(int(result["sample_count"]) for result in trainer_results.values())
        expected_bias = sum(float(result["bias"]) * int(result["sample_count"]) for result in trainer_results.values()) / total_samples
        expected_weights = []
        weight_count = len(next(iter(trainer_results.values()))["weights"])
        for index in range(weight_count):
            expected_weights.append(
                sum(float(result["weights"][index]) * int(result["sample_count"]) for result in trainer_results.values()) / total_samples
            )
        assert isclose(float(aggregated_model["bias"]), expected_bias, rel_tol=1e-9)
        for actual, expected in zip(aggregated_model["weights"], expected_weights):
            assert isclose(float(actual), expected, rel_tol=1e-9)

        evaluation_tasks = list(container.evaluation_task_repository(session).list_by_round(round_id))
        assert len(evaluation_tasks) == 1
        evaluation_task = evaluation_tasks[0]
        assert evaluation_task.target_model_artifact_uri == round_after_aggregation.aggregated_model_artifact_uri

        eval_claim_service = EvaluationClaimService(container.evaluation_task_repository(session), container.node_repository(session))
        eval_completion_service = EvaluationCompletionService(
            tasks=container.evaluation_task_repository(session),
            artifacts=container.artifact_repository(session),
            reports=container.evaluation_report_repository(session),
            jobs=container.job_repository(session),
        )
        claimed_eval = eval_claim_service.claim_next("evaluator-1")
        assert claimed_eval is not None
        eval_executor = EvaluationExecutor()
        eval_dataset_payload = artifact_service.read_content(claimed_eval.dataset_artifact_uri.split("artifact://", 1)[1])
        eval_artifacts = eval_executor.execute(
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
        round_after_eval = reconcile_service.reconcile(round_id)
        assert round_after_eval.status == RoundStatus.COMPLETED
        assert container.job_repository(session).get(101).offchain_status == OffchainJobStatus.READY_FOR_ATTESTATION
    finally:
        session.close()


def test_round_reconciliation_fails_on_malformed_trainer_output(app) -> None:
    container = app.state.container
    session = container.session_factory()
    try:
        container.job_repository(session).upsert(
            Job(
                job_id=102,
                requester="0x00000000000000000000000000000000000000a1",
                provider="0x00000000000000000000000000000000000000b2",
                attestor="0x00000000000000000000000000000000000000c3",
                target_escrow_wei=10,
                escrow_balance_wei=10,
                job_spec_hash="0x" + "2" * 64,
                onchain_status=OnchainJobStatus.FUNDED,
                offchain_status=OffchainJobStatus.SCHEDULING,
            )
        )
        _register_online_nodes(container, session)
        artifact_service = _artifact_service(container, session)
        protocol = FedAvgLikeV1Protocol(
            jobs=container.job_repository(session),
            nodes=container.node_repository(session),
            rounds=container.round_repository(session),
            training_tasks=container.training_task_repository(session),
            evaluation_tasks=container.evaluation_task_repository(session),
            artifacts=artifact_service,
            aggregation=FedAvgLikeAggregationService(artifact_service),
        )
        registry = ProtocolRegistry([protocol])
        run_service = ProtocolRunService(jobs=container.job_repository(session), protocols=registry)
        result = run_service.start_for_job(102)
        round_id = result.round_record.round_id

        claim_service = TaskClaimService(container.training_task_repository(session), container.node_repository(session))
        completion_service = TaskCompletionService(container.training_task_repository(session), container.artifact_repository(session))
        fit_executor = LocalFitExecutor()
        claimed_one = claim_service.claim_next("trainer-1")
        claimed_two = claim_service.claim_next("trainer-2")
        assert claimed_one is not None and claimed_two is not None

        model_payload = artifact_service.read_content(claimed_one.model_artifact_uri.split("artifact://", 1)[1])
        dataset_one = artifact_service.read_content(claimed_one.dataset_artifact_uri.split("artifact://", 1)[1])
        execution = fit_executor.execute(
            task=_training_record(claimed_one),
            trainer_node_id="trainer-1",
            model_payload=model_payload,
            dataset_payload=dataset_one,
        )
        valid_result = artifact_service.upload(
            kind=ArtifactKind.TASK_RESULT,
            name=f"{claimed_one.task_id}-result.json",
            payload=execution.result_payload,
            mime_type="application/json",
            metadata={"round_id": round_id},
            job_id=claimed_one.job_id,
            task_id=claimed_one.task_id,
        )
        valid_report = artifact_service.upload(
            kind=ArtifactKind.TRAINER_REPORT,
            name=f"{claimed_one.task_id}-report.json",
            payload=execution.report_payload,
            mime_type="application/json",
            metadata={"round_id": round_id},
            job_id=claimed_one.job_id,
            task_id=claimed_one.task_id,
        )
        completion_service.complete(claimed_one.task_id, "trainer-1", valid_result.artifact_id, valid_report.artifact_id)

        bad_result = artifact_service.upload(
            kind=ArtifactKind.TASK_RESULT,
            name=f"{claimed_two.task_id}-result.json",
            payload=json.dumps({"bias": 1.0, "sample_count": 4}).encode("utf-8"),
            mime_type="application/json",
            metadata={"round_id": round_id},
            job_id=claimed_two.job_id,
            task_id=claimed_two.task_id,
        )
        bad_report = artifact_service.upload(
            kind=ArtifactKind.TRAINER_REPORT,
            name=f"{claimed_two.task_id}-report.json",
            payload=json.dumps({"status": "malformed"}).encode("utf-8"),
            mime_type="application/json",
            metadata={"round_id": round_id},
            job_id=claimed_two.job_id,
            task_id=claimed_two.task_id,
        )
        completion_service.complete(claimed_two.task_id, "trainer-2", bad_result.artifact_id, bad_report.artifact_id)

        reconcile_service = RoundReconciliationService(
            rounds=container.round_repository(session),
            jobs=container.job_repository(session),
            training_tasks=container.training_task_repository(session),
            evaluation_tasks=container.evaluation_task_repository(session),
            evaluation_reports=container.evaluation_report_repository(session),
            protocols=registry,
        )
        round_after_failure = reconcile_service.reconcile(round_id)
        assert round_after_failure.status == RoundStatus.FAILED
        assert "malformed trainer result" in (round_after_failure.failure_reason or "")
        assert container.job_repository(session).get(102).offchain_status == OffchainJobStatus.FAILED
    finally:
        session.close()
