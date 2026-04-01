from __future__ import annotations

import base64
import json

from orchestrator.app.api.routes.artifacts import upload_artifact
from orchestrator.app.api.routes.internal import seed_demo_tasks_for_job
from orchestrator.app.api.routes.nodes import heartbeat_node, register_node
from orchestrator.app.api.routes.trainer_tasks import claim_task, complete_task, fail_task, get_task
from orchestrator.app.application.dto import (
    ArtifactUploadRequest,
    NodeHeartbeatRequest,
    NodeRegistrationRequest,
    TaskClaimRequest,
    TaskCompleteRequest,
    TaskFailRequest,
)
from orchestrator.app.application.services import (
    ArtifactService,
    NodeRegistryService,
    TaskClaimService,
    TaskCompletionService,
    TaskDispatchService,
)
from orchestrator.app.domain.entities import Job
from orchestrator.app.domain.enums import OffchainJobStatus, OnchainJobStatus



def test_seed_claim_upload_and_complete_task_flow(app) -> None:
    container = app.state.container
    session = container.session_factory()
    try:
        container.job_repository(session).upsert(
            Job(
                job_id=1,
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

        registry = NodeRegistryService(container.node_repository(session))
        for node_id in ("trainer-1", "trainer-2"):
            register_node(
                NodeRegistrationRequest(
                    node_id=node_id,
                    role="trainer",
                    endpoint_url=f"http://{node_id}.local/callback",
                    capabilities={"cpu": True},
                ),
                registry,
            )
            heartbeat_node(NodeHeartbeatRequest(node_id=node_id), registry)

        dispatch = TaskDispatchService(
            jobs=container.job_repository(session),
            nodes=container.node_repository(session),
            tasks=container.training_task_repository(session),
            artifacts=ArtifactService(container.artifact_repository(session), container.artifact_storage),
        )
        seeded = seed_demo_tasks_for_job(1, dispatch)
        assert seeded.job_id == 1
        assert len(seeded.task_ids) == 2

        claim_service = TaskClaimService(container.training_task_repository(session), container.node_repository(session))
        claimed_one = claim_task(TaskClaimRequest(trainer_node_id="trainer-1"), claim_service)
        claimed_two = claim_task(TaskClaimRequest(trainer_node_id="trainer-2"), claim_service)
        assert claimed_one is not None
        assert claimed_two is not None
        assert claimed_one.task_id != claimed_two.task_id

        artifact_service = ArtifactService(container.artifact_repository(session), container.artifact_storage)
        result_artifact = upload_artifact(
            ArtifactUploadRequest(
                kind="task_result",
                name="result.json",
                payload_base64=base64.b64encode(json.dumps({"weights": [1, 2, 3]}).encode("utf-8")).decode("utf-8"),
                mime_type="application/json",
                metadata={"kind": "result"},
                job_id=1,
                task_id=claimed_one.task_id,
            ),
            artifact_service,
        )
        report_artifact = upload_artifact(
            ArtifactUploadRequest(
                kind="trainer_report",
                name="report.json",
                payload_base64=base64.b64encode(json.dumps({"accuracy": 1.0}).encode("utf-8")).decode("utf-8"),
                mime_type="application/json",
                metadata={"kind": "report"},
                job_id=1,
                task_id=claimed_one.task_id,
            ),
            artifact_service,
        )

        completion = TaskCompletionService(container.training_task_repository(session), container.artifact_repository(session))
        completed = complete_task(
            claimed_one.task_id,
            TaskCompleteRequest(
                trainer_node_id="trainer-1",
                result_artifact_id=result_artifact.artifact_id,
                report_artifact_id=report_artifact.artifact_id,
            ),
            completion,
        )
        assert completed.status == "completed"
        fetched = get_task(claimed_one.task_id, completion)
        assert fetched.result_artifact_uri == result_artifact.uri
        assert fetched.report_artifact_uri == report_artifact.uri
        assert len(container.artifact_repository(session).list_by_task(claimed_one.task_id)) == 2
    finally:
        session.close()



def test_task_can_fail_cleanly(app) -> None:
    container = app.state.container
    session = container.session_factory()
    try:
        container.job_repository(session).upsert(
            Job(
                job_id=2,
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
        registry = NodeRegistryService(container.node_repository(session))
        register_node(
            NodeRegistrationRequest(
                node_id="trainer-9",
                role="trainer",
                endpoint_url="http://trainer-9.local/callback",
                capabilities=None,
            ),
            registry,
        )
        heartbeat_node(NodeHeartbeatRequest(node_id="trainer-9"), registry)
        dispatch = TaskDispatchService(
            jobs=container.job_repository(session),
            nodes=container.node_repository(session),
            tasks=container.training_task_repository(session),
            artifacts=ArtifactService(container.artifact_repository(session), container.artifact_storage),
        )
        seeded = seed_demo_tasks_for_job(2, dispatch)
        claim_service = TaskClaimService(container.training_task_repository(session), container.node_repository(session))
        claimed = claim_task(TaskClaimRequest(trainer_node_id="trainer-9"), claim_service)
        assert claimed is not None
        completion = TaskCompletionService(container.training_task_repository(session), container.artifact_repository(session))
        failed = fail_task(
            claimed.task_id,
            TaskFailRequest(trainer_node_id="trainer-9", failure_reason="demo execution failure"),
            completion,
        )
        assert failed.status == "failed"
        assert failed.failure_reason == "demo execution failure"
        assert seeded.task_ids == [claimed.task_id]
    finally:
        session.close()
