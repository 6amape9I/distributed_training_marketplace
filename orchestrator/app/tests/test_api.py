from fastapi import HTTPException

from orchestrator.app.api.routes.jobs import get_job, list_jobs, sync_jobs
from orchestrator.app.api.routes.nodes import get_node, heartbeat_node, list_nodes, register_node
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
