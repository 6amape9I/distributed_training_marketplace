from __future__ import annotations

from orchestrator.app.domain.enums import OffchainJobStatus, OnchainJobStatus


class InvalidLifecycleTransition(ValueError):
    pass


_ALLOWED_TRANSITIONS: dict[OffchainJobStatus, set[OffchainJobStatus]] = {
    OffchainJobStatus.DISCOVERED: {
        OffchainJobStatus.AWAITING_FUNDING,
        OffchainJobStatus.FUNDED,
        OffchainJobStatus.ATTESTED,
        OffchainJobStatus.FINALIZED,
        OffchainJobStatus.FAILED,
    },
    OffchainJobStatus.AWAITING_FUNDING: {
        OffchainJobStatus.FUNDED,
        OffchainJobStatus.ATTESTED,
        OffchainJobStatus.FINALIZED,
        OffchainJobStatus.FAILED,
    },
    OffchainJobStatus.FUNDED: {
        OffchainJobStatus.READY_FOR_SCHEDULING,
        OffchainJobStatus.ATTESTED,
        OffchainJobStatus.FINALIZED,
        OffchainJobStatus.FAILED,
    },
    OffchainJobStatus.READY_FOR_SCHEDULING: {
        OffchainJobStatus.SCHEDULING,
        OffchainJobStatus.ATTESTED,
        OffchainJobStatus.FINALIZED,
        OffchainJobStatus.FAILED,
    },
    OffchainJobStatus.SCHEDULING: {
        OffchainJobStatus.AWAITING_ATTESTATION,
        OffchainJobStatus.ATTESTED,
        OffchainJobStatus.FINALIZED,
        OffchainJobStatus.FAILED,
    },
    OffchainJobStatus.AWAITING_ATTESTATION: {
        OffchainJobStatus.ATTESTED,
        OffchainJobStatus.SETTLEMENT_PENDING,
        OffchainJobStatus.FINALIZED,
        OffchainJobStatus.FAILED,
    },
    OffchainJobStatus.ATTESTED: {
        OffchainJobStatus.SETTLEMENT_PENDING,
        OffchainJobStatus.FINALIZED,
        OffchainJobStatus.FAILED,
    },
    OffchainJobStatus.SETTLEMENT_PENDING: {OffchainJobStatus.FINALIZED, OffchainJobStatus.FAILED},
    OffchainJobStatus.FINALIZED: set(),
    OffchainJobStatus.FAILED: set(),
}


class JobLifecycleService:
    def transition(self, current: OffchainJobStatus, target: OffchainJobStatus) -> OffchainJobStatus:
        if current == target:
            return current
        if target not in _ALLOWED_TRANSITIONS[current]:
            raise InvalidLifecycleTransition(f"Cannot move job from {current.value} to {target.value}")
        return target

    def status_for_created_job(self) -> OffchainJobStatus:
        return OffchainJobStatus.DISCOVERED

    def status_for_funding(self, is_fully_funded: bool) -> OffchainJobStatus:
        return OffchainJobStatus.FUNDED if is_fully_funded else OffchainJobStatus.AWAITING_FUNDING

    def status_for_onchain_progress(self, onchain_status: OnchainJobStatus) -> OffchainJobStatus:
        if onchain_status is OnchainJobStatus.OPEN:
            return OffchainJobStatus.AWAITING_FUNDING
        if onchain_status is OnchainJobStatus.FUNDED:
            return OffchainJobStatus.FUNDED
        if onchain_status is OnchainJobStatus.ATTESTED:
            return OffchainJobStatus.ATTESTED
        if onchain_status is OnchainJobStatus.FINALIZED:
            return OffchainJobStatus.FINALIZED
        raise InvalidLifecycleTransition(f"Unsupported on-chain status: {onchain_status}")

    def prepare_for_scheduling(
        self,
        current: OffchainJobStatus,
        *,
        has_trainers: bool,
        has_evaluator: bool,
    ) -> OffchainJobStatus:
        if not (has_trainers and has_evaluator):
            return current
        if current is OffchainJobStatus.FUNDED:
            return self.transition(current, OffchainJobStatus.READY_FOR_SCHEDULING)
        if current is OffchainJobStatus.READY_FOR_SCHEDULING:
            return self.transition(current, OffchainJobStatus.SCHEDULING)
        return current

    def mark_sync_failure(self, current: OffchainJobStatus) -> OffchainJobStatus:
        if current in {OffchainJobStatus.FINALIZED, OffchainJobStatus.FAILED}:
            return current
        return self.transition(current, OffchainJobStatus.FAILED)
