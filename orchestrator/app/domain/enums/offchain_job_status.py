from enum import StrEnum


class OffchainJobStatus(StrEnum):
    DISCOVERED = "discovered"
    AWAITING_FUNDING = "awaiting_funding"
    FUNDED = "funded"
    READY_FOR_SCHEDULING = "ready_for_scheduling"
    SCHEDULING = "scheduling"
    AWAITING_ATTESTATION = "awaiting_attestation"
    ATTESTED = "attested"
    SETTLEMENT_PENDING = "settlement_pending"
    FINALIZED = "finalized"
    FAILED = "failed"
