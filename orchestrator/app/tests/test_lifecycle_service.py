import pytest

from orchestrator.app.application.services import InvalidLifecycleTransition, JobLifecycleService
from orchestrator.app.domain.enums import OffchainJobStatus, OnchainJobStatus


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (OffchainJobStatus.DISCOVERED, OffchainJobStatus.AWAITING_FUNDING),
        (OffchainJobStatus.FUNDED, OffchainJobStatus.READY_FOR_SCHEDULING),
        (OffchainJobStatus.READY_FOR_SCHEDULING, OffchainJobStatus.SCHEDULING),
        (OffchainJobStatus.SCHEDULING, OffchainJobStatus.ATTESTED),
        (OffchainJobStatus.ATTESTED, OffchainJobStatus.FINALIZED),
    ],
)
def test_transition_allows_stage2_paths(current: OffchainJobStatus, target: OffchainJobStatus) -> None:
    service = JobLifecycleService()
    assert service.transition(current, target) is target


def test_transition_rejects_invalid_jump() -> None:
    service = JobLifecycleService()
    with pytest.raises(InvalidLifecycleTransition):
        service.transition(OffchainJobStatus.DISCOVERED, OffchainJobStatus.SETTLEMENT_PENDING)


@pytest.mark.parametrize(
    ("onchain_status", "expected"),
    [
        (OnchainJobStatus.OPEN, OffchainJobStatus.AWAITING_FUNDING),
        (OnchainJobStatus.FUNDED, OffchainJobStatus.FUNDED),
        (OnchainJobStatus.ATTESTED, OffchainJobStatus.ATTESTED),
        (OnchainJobStatus.FINALIZED, OffchainJobStatus.FINALIZED),
    ],
)
def test_status_for_onchain_progress_maps_explicitly(
    onchain_status: OnchainJobStatus,
    expected: OffchainJobStatus,
) -> None:
    service = JobLifecycleService()
    assert service.status_for_onchain_progress(onchain_status) is expected
