from __future__ import annotations

from .job_sync_service import JobSyncService, SyncRunResult
from .scheduling_preparation_service import SchedulingPreparationService


class OrchestrationCoordinator:
    def __init__(self, *, sync_service: JobSyncService, scheduling_service: SchedulingPreparationService) -> None:
        self.sync_service = sync_service
        self.scheduling_service = scheduling_service

    def run_sync_once(self) -> SyncRunResult:
        return self.sync_service.run_once()

    def reconcile_lifecycle(self) -> int:
        return self.scheduling_service.reconcile()
