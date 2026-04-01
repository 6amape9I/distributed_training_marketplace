from __future__ import annotations

from typing import Any

from web3 import Web3
from web3.contract import Contract
from web3.exceptions import Web3Exception

from orchestrator.app.domain.enums import OnchainJobStatus
from orchestrator.app.infrastructure.blockchain.abi import TRAINING_MARKETPLACE_ABI
from orchestrator.app.infrastructure.blockchain.types import ChainEvent, ChainJobSnapshot


class TrainingMarketplaceClient:
    def __init__(self, *, rpc_url: str, contract_address: str) -> None:
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.contract: Contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=TRAINING_MARKETPLACE_ABI,
        )

    def get_chain_id(self) -> int:
        return int(self.w3.eth.chain_id)

    def get_latest_block(self) -> int:
        return int(self.w3.eth.block_number)

    def get_status(self) -> dict[str, object]:
        try:
            return {
                "reachable": True,
                "chain_id": self.get_chain_id(),
                "latest_block": self.get_latest_block(),
                "rpc_url": self.rpc_url,
            }
        except Web3Exception as exc:
            return {"reachable": False, "error": str(exc), "rpc_url": self.rpc_url}

    def fetch_events(self, *, from_block: int, to_block: int) -> list[ChainEvent]:
        events: list[ChainEvent] = []
        for event_name in (
            "JobCreated",
            "JobFunded",
            "JobFullyFunded",
            "AttestationSubmitted",
            "JobFinalized",
            "PayoutWithdrawn",
            "RefundWithdrawn",
        ):
            event_abi = getattr(self.contract.events, event_name)
            for raw_event in event_abi().get_logs(from_block=from_block, to_block=to_block):
                args = {key: self._normalize_value(value) for key, value in dict(raw_event["args"]).items()}
                events.append(
                    ChainEvent(
                        event_name=event_name,
                        block_number=int(raw_event["blockNumber"]),
                        transaction_hash=self._normalize_value(raw_event["transactionHash"]),
                        log_index=int(raw_event["logIndex"]),
                        args=args,
                    )
                )
        events.sort(key=lambda item: (item.block_number, item.log_index))
        return events

    def get_job(self, job_id: int) -> ChainJobSnapshot:
        job = self.contract.functions.getJob(job_id).call()
        return ChainJobSnapshot(
            job_id=job_id,
            requester=job[0],
            provider=job[1],
            attestor=job[2],
            target_escrow_wei=int(job[3]),
            escrow_balance_wei=int(job[4]),
            job_spec_hash=self._normalize_optional_hash(job[5]),
            attestation_hash=self._normalize_optional_hash(job[6]),
            settlement_hash=self._normalize_optional_hash(job[7]),
            provider_payout_wei=int(job[8]),
            requester_refund_wei=int(job[9]),
            onchain_status=OnchainJobStatus(("open", "funded", "attested", "finalized")[int(job[10])]),
        )

    def _normalize_optional_hash(self, value: Any) -> str | None:
        normalized = self._normalize_value(value)
        if normalized == "0x" + "0" * 64:
            return None
        return normalized

    def _normalize_value(self, value: Any) -> Any:
        if isinstance(value, (bytes, bytearray)):
            return Web3.to_hex(value)
        if hasattr(value, "hex") and callable(value.hex):
            try:
                return Web3.to_hex(value)
            except TypeError:
                return value.hex()
        return value
