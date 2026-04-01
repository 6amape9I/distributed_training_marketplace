from enum import StrEnum


class JobRole(StrEnum):
    REQUESTER = "requester"
    PROVIDER = "provider"
    ATTESTOR = "attestor"
