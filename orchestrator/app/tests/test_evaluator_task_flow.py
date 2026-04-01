from __future__ import annotations

import base64
import json

from orchestrator.app.api.routes.artifacts import upload_artifact
from orchestrator.app.api.routes.evaluator_tasks import claim_evaluation_task, complete_evaluation_task, get_evaluation_task
from orchestrator.app.api.routes.internal import seed_evaluation_tasks_for_job
from orchestrator.app.api.routes.nodes import heartbeat_node, register_node
from orchestrator.app.application.dto import (
    ArtifactUploadRequest,
    EvaluationTaskClaimRequest,
    EvaluationTaskCompleteRequest,
    NodeHeartbeatRequest,
    NodeRegistrationRequest,
)
from orchestrator.app.application.services import (
    ArtifactService,
    EvaluationClaimService,
    EvaluationCompletionService,
    EvaluationDispatchService,
    NodeRegistryService,
)
from orchestrator.app.domain.entities import Job, TrainingTask
from orchestrator.app.domain.enums import OffchainJobStatus, OnchainJobStatus, TrainingTaskStatus, TrainingTaskType


def test_seed_claim_complete_evaluation_flow_and_promote_job(app) -> None:
    container = app.state.container
    session = container.session_factory()
    try:
        container.job_repository(session).upsert(
            Job(
                job_id=10,
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
        task_repo = container.training_task_repository(session)
        task_repo.upsert(
            TrainingTask(
                task_id="task-1",
                job_id=10,
                round_id=None,
                trainer_node_id="trainer-1",
                task_type=TrainingTaskType.LOCAL_FIT,
                status=TrainingTaskStatus.COMPLETED,
                data_partition_id="partition-1",
                model_artifact_uri="artifact://result-1",
                dataset_artifact_uri="artifact://dataset-1",
                config_json={"feature_count": 5},
                result_artifact_uri="artifact://result-1",
                result_artifact_hash="hash-1",
                report_artifact_uri="artifact://report-1",
                report_artifact_hash="hash-2",
            )
        )
        registry = NodeRegistryService(container.node_repository(session))
        register_node(
            NodeRegistrationRequest(
                node_id="evaluator-1",
                role="evaluator",
                endpoint_url="http://evaluator-1.local/callback",
                capabilities={"metrics": ["accuracy"]},
            ),
            registry,
        )
        heartbeat_node(NodeHeartbeatRequest(node_id="evaluator-1"), registry)

        dispatch = EvaluationDispatchService(
            jobs=container.job_repository(session),
            nodes=container.node_repository(session),
            training_tasks=container.training_task_repository(session),
            evaluation_tasks=container.evaluation_task_repository(session),
            artifacts=ArtifactService(container.artifact_repository(session), container.artifact_storage),
        )
        seeded = seed_evaluation_tasks_for_job(10, dispatch)
        assert seeded.job_id == 10
        assert len(seeded.evaluation_task_ids) == 1

        claim_service = EvaluationClaimService(
            container.evaluation_task_repository(session),
            container.node_repository(session),
        )
        claimed = claim_evaluation_task(EvaluationTaskClaimRequest(evaluator_node_id="evaluator-1"), claim_service)
        assert claimed is not None

        artifact_service = ArtifactService(container.artifact_repository(session), container.artifact_storage)
        report_artifact = upload_artifact(
            ArtifactUploadRequest(
                kind="evaluation_report",
                name="evaluation-report.json",
                payload_base64=base64.b64encode(
                    json.dumps({"accuracy": 1.0, "average_loss": 0.1, "accepted": True}).encode("utf-8")
                ).decode("utf-8"),
                mime_type="application/json",
                metadata={"kind": "evaluation_report"},
                job_id=10,
                task_id=claimed.evaluation_task_id,
            ),
            artifact_service,
        )

        completion = EvaluationCompletionService(
            tasks=container.evaluation_task_repository(session),
            artifacts=container.artifact_repository(session),
            reports=container.evaluation_report_repository(session),
            jobs=container.job_repository(session),
        )
        completed = complete_evaluation_task(
            claimed.evaluation_task_id,
            EvaluationTaskCompleteRequest(
                evaluator_node_id="evaluator-1",
                report_artifact_id=report_artifact.artifact_id,
                metrics_json={"accuracy": 1.0, "average_loss": 0.1, "accepted": True},
                sample_count=4,
                acceptance_decision=True,
                target_model_digest="digest-1",
            ),
            completion,
        )
        assert completed.status == "completed"
        fetched = get_evaluation_task(claimed.evaluation_task_id, completion)
        assert fetched.report_artifact_uri == report_artifact.uri
        assert container.job_repository(session).get(10).offchain_status == OffchainJobStatus.READY_FOR_ATTESTATION
    finally:
        session.close()
