from enum import StrEnum


class OnchainJobStatus(StrEnum):
    OPEN = "open"
    FUNDED = "funded"
    ATTESTED = "attested"
    FINALIZED = "finalized"
