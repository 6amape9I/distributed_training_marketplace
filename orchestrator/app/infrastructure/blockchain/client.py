from dataclasses import dataclass


@dataclass(slots=True)
class BlockchainClient:
    rpc_url: str
