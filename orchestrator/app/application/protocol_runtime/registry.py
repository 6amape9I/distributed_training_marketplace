from __future__ import annotations

from orchestrator.app.application.protocols.training_protocol import TrainingProtocol


class ProtocolRegistryError(ValueError):
    pass


class ProtocolRegistry:
    def __init__(self, protocols: list[TrainingProtocol]) -> None:
        self._protocols = {protocol.protocol_name: protocol for protocol in protocols}

    def get(self, protocol_name: str) -> TrainingProtocol:
        protocol = self._protocols.get(protocol_name)
        if protocol is None:
            raise ProtocolRegistryError(f"protocol '{protocol_name}' is not registered")
        return protocol

    def default(self) -> TrainingProtocol:
        if not self._protocols:
            raise ProtocolRegistryError("no training protocols are registered")
        return next(iter(self._protocols.values()))
