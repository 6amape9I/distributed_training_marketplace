from enum import StrEnum


class NodeStatus(StrEnum):
    REGISTERED = "registered"
    ONLINE = "online"
    STALE = "stale"
    OFFLINE = "offline"
