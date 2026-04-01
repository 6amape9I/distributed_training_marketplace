from enum import StrEnum


class JobStatus(StrEnum):
    OPEN = "open"
    FUNDED = "funded"
    ATTESTED = "attested"
    FINALIZED = "finalized"
