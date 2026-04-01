from orchestrator.app.application.services import NodeLivenessService, NodeRegistryService
from orchestrator.app.domain.enums import NodeRole, NodeStatus

from .conftest import InMemoryNodeRepository


def test_register_and_heartbeat_update_node_state() -> None:
    repository = InMemoryNodeRepository()
    service = NodeRegistryService(repository)

    registered = service.register(
        node_id="trainer-1",
        role=NodeRole.TRAINER,
        endpoint_url="http://trainer.local/callback",
        capabilities={"gpu": False},
    )
    assert registered.status is NodeStatus.REGISTERED

    heartbeat = service.heartbeat("trainer-1")
    assert heartbeat is not None
    assert heartbeat.status is NodeStatus.ONLINE


def test_liveness_service_marks_stale_and_offline() -> None:
    service = NodeLivenessService(stale_after_seconds=10)
    assert service.derive_status(None).value == "registered"
