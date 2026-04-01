from typing import Protocol

from shared.python.ids import JobId
from shared.python.schemas import SettlementDecision


class PayoutPolicy(Protocol):
    def decide(self, job_id: JobId, accepted: bool, escrow_wei: int) -> SettlementDecision: ...
