from orchestrator.app.api.main import app
from orchestrator.app.api.routes.health import health
from orchestrator.app.api.routes.jobs import list_jobs
from orchestrator.app.api.routes.nodes import list_nodes
from orchestrator.app.infrastructure.settings import get_settings


def test_app_registers_stage1_routes() -> None:
    route_paths = {route.path for route in app.routes}
    assert "/health" in route_paths
    assert "/jobs" in route_paths
    assert "/nodes" in route_paths


def test_placeholder_handlers_return_expected_payloads() -> None:
    health_payload = health(get_settings())
    jobs_payload = list_jobs()
    nodes_payload = list_nodes()

    assert health_payload["status"] == "ok"
    assert jobs_payload[0].status == "open"
    assert nodes_payload[0].state == "placeholder"
