from enum import StrEnum


class OffchainJobStatus(StrEnum):
    DISCOVERED = "discovered"
    AWAITING_FUNDING = "awaiting_funding"
    FUNDED = "funded"
    READY_FOR_SCHEDULING = "ready_for_scheduling"
    SCHEDULING = "scheduling"
    EVALUATING = "evaluating"
    READY_FOR_ATTESTATION = "ready_for_attestation"
    EVALUATION_FAILED = "evaluation_failed"
    AWAITING_ATTESTATION = "awaiting_attestation"
    ATTESTED = "attested"
    SETTLEMENT_PENDING = "settlement_pending"
    FINALIZED = "finalized"
    FAILED = "failed"
