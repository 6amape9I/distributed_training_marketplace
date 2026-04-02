from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from eth_utils import keccak, to_checksum_address
from web3 import Web3


DEFAULT_PUBLIC_NETWORK = "base-sepolia"
DEFAULT_PUBLIC_CHAIN_ID = 84532
SUCCESS_PROVIDER_BPS = 9000
SUCCESS_REQUESTER_BPS = 1000
ZERO_HASH = "0x" + "0" * 64
JOB_STATUS_MAP = {
    0: "open",
    1: "funded",
    2: "attested",
    3: "finalized",
}


def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))


def keccak_text(value: str) -> str:
    return "0x" + keccak(text=value).hex()


def compute_success_split(escrow_balance_wei: int) -> tuple[int, int]:
    if escrow_balance_wei < 0:
        raise ValueError("escrow_balance_wei must be non-negative")
    provider_payout = escrow_balance_wei * SUCCESS_PROVIDER_BPS // 10_000
    requester_refund = escrow_balance_wei - provider_payout
    return provider_payout, requester_refund


def build_attestation_payload(
    *,
    network: str,
    chain_id: int,
    contract_address: str,
    job: dict[str, Any],
    round_record: dict[str, Any],
    evaluation_task: dict[str, Any],
) -> dict[str, Any]:
    return {
        "version": "stage7_attestation_v1",
        "network": network,
        "chain_id": chain_id,
        "contract_address": contract_address.lower(),
        "job_id": int(job["job_id"]),
        "job_spec_hash": str(job["job_spec_hash"]).lower(),
        "requester": str(job["requester"]).lower(),
        "provider": str(job["provider"]).lower(),
        "attestor": str(job["attestor"]).lower(),
        "offchain_outcome": str(job["offchain_status"]),
        "round_id": str(round_record["round_id"]),
        "round_index": int(round_record["round_index"]),
        "aggregated_model_artifact_uri": round_record["aggregated_model_artifact_uri"],
        "aggregated_model_artifact_hash": round_record["aggregated_model_artifact_hash"],
        "evaluation_report_id": round_record.get("evaluation_report_id"),
        "evaluation_task_id": evaluation_task["evaluation_task_id"],
        "evaluation_report_artifact_uri": evaluation_task["report_artifact_uri"],
        "evaluation_report_artifact_hash": evaluation_task["report_artifact_hash"],
    }


def build_attestation_artifact(
    *,
    network: str,
    chain_id: int,
    contract_address: str,
    job: dict[str, Any],
    round_record: dict[str, Any],
    evaluation_task: dict[str, Any],
) -> dict[str, Any]:
    payload = build_attestation_payload(
        network=network,
        chain_id=chain_id,
        contract_address=contract_address,
        job=job,
        round_record=round_record,
        evaluation_task=evaluation_task,
    )
    return {
        "payload": payload,
        "canonical_json": canonical_json(payload),
        "hash": keccak_text(canonical_json(payload)),
    }


def build_settlement_payload(
    *,
    network: str,
    chain_id: int,
    contract_address: str,
    job: dict[str, Any],
    round_record: dict[str, Any],
    attestation_hash: str,
    provider_payout_wei: int,
    requester_refund_wei: int,
    policy: str = "success_90_10",
) -> dict[str, Any]:
    return {
        "version": "stage7_settlement_v1",
        "network": network,
        "chain_id": chain_id,
        "contract_address": contract_address.lower(),
        "job_id": int(job["job_id"]),
        "requester": str(job["requester"]).lower(),
        "provider": str(job["provider"]).lower(),
        "attestor": str(job["attestor"]).lower(),
        "round_id": str(round_record["round_id"]),
        "offchain_outcome": str(job["offchain_status"]),
        "attestation_hash": attestation_hash.lower(),
        "escrow_balance_wei": int(job["escrow_balance_wei"]),
        "provider_payout_wei": int(provider_payout_wei),
        "requester_refund_wei": int(requester_refund_wei),
        "policy": policy,
    }


def build_settlement_artifact(
    *,
    network: str,
    chain_id: int,
    contract_address: str,
    job: dict[str, Any],
    round_record: dict[str, Any],
    attestation_hash: str,
    provider_payout_wei: int,
    requester_refund_wei: int,
    policy: str = "success_90_10",
) -> dict[str, Any]:
    payload = build_settlement_payload(
        network=network,
        chain_id=chain_id,
        contract_address=contract_address,
        job=job,
        round_record=round_record,
        attestation_hash=attestation_hash,
        provider_payout_wei=provider_payout_wei,
        requester_refund_wei=requester_refund_wei,
        policy=policy,
    )
    return {
        "payload": payload,
        "canonical_json": canonical_json(payload),
        "hash": keccak_text(canonical_json(payload)),
    }


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_abi_path() -> Path:
    return repo_root() / "contracts" / "out" / "ITrainingMarketplace.sol" / "ITrainingMarketplace.json"


def _load_abi(path: Path | None = None) -> list[dict[str, Any]]:
    abi_path = path or default_abi_path()
    payload = json.loads(abi_path.read_text(encoding="utf-8"))
    return payload["abi"]


def _normalize_optional_hash(value: str) -> str | None:
    value = value.lower()
    if value == ZERO_HASH:
        return None
    return value


def fetch_onchain_job(*, rpc_url: str, contract_address: str, job_id: int, abi_path: Path | None = None) -> dict[str, Any]:
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise RuntimeError(f"failed to connect to RPC: {rpc_url}")

    contract = web3.eth.contract(address=to_checksum_address(contract_address), abi=_load_abi(abi_path))
    job = contract.functions.getJob(job_id).call()

    return {
        "chain_id": web3.eth.chain_id,
        "contract_address": to_checksum_address(contract_address),
        "job_id": int(job_id),
        "requester": job[0],
        "provider": job[1],
        "attestor": job[2],
        "target_escrow_wei": int(job[3]),
        "escrow_balance_wei": int(job[4]),
        "job_spec_hash": Web3.to_hex(job[5]).lower(),
        "attestation_hash": _normalize_optional_hash(Web3.to_hex(job[6])),
        "settlement_hash": _normalize_optional_hash(Web3.to_hex(job[7])),
        "provider_payout_wei": int(job[8]),
        "requester_refund_wei": int(job[9]),
        "status": JOB_STATUS_MAP[int(job[10])],
    }


def _read_json(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _command_attestation(args: argparse.Namespace) -> int:
    result = build_attestation_artifact(
        network=args.network,
        chain_id=args.chain_id,
        contract_address=args.contract_address,
        job=_read_json(args.job_json),
        round_record=_read_json(args.round_json),
        evaluation_task=_read_json(args.evaluation_json),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _command_settlement(args: argparse.Namespace) -> int:
    job = _read_json(args.job_json)
    if args.provider_payout_wei is None or args.requester_refund_wei is None:
        provider_payout_wei, requester_refund_wei = compute_success_split(int(job["escrow_balance_wei"]))
    else:
        provider_payout_wei = int(args.provider_payout_wei)
        requester_refund_wei = int(args.requester_refund_wei)
    result = build_settlement_artifact(
        network=args.network,
        chain_id=args.chain_id,
        contract_address=args.contract_address,
        job=job,
        round_record=_read_json(args.round_json),
        attestation_hash=args.attestation_hash,
        provider_payout_wei=provider_payout_wei,
        requester_refund_wei=requester_refund_wei,
        policy=args.policy,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _command_split(args: argparse.Namespace) -> int:
    provider_payout_wei, requester_refund_wei = compute_success_split(args.escrow_balance_wei)
    print(
        json.dumps(
            {
                "provider_payout_wei": provider_payout_wei,
                "requester_refund_wei": requester_refund_wei,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _command_onchain_job(args: argparse.Namespace) -> int:
    result = fetch_onchain_job(
        rpc_url=args.rpc_url,
        contract_address=args.contract_address,
        job_id=args.job_id,
        abi_path=Path(args.abi_path) if args.abi_path else None,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage 7 public demo helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    attestation = subparsers.add_parser("attestation")
    attestation.add_argument("--network", default=DEFAULT_PUBLIC_NETWORK)
    attestation.add_argument("--chain-id", type=int, default=DEFAULT_PUBLIC_CHAIN_ID)
    attestation.add_argument("--contract-address", required=True)
    attestation.add_argument("--job-json", required=True)
    attestation.add_argument("--round-json", required=True)
    attestation.add_argument("--evaluation-json", required=True)
    attestation.set_defaults(func=_command_attestation)

    settlement = subparsers.add_parser("settlement")
    settlement.add_argument("--network", default=DEFAULT_PUBLIC_NETWORK)
    settlement.add_argument("--chain-id", type=int, default=DEFAULT_PUBLIC_CHAIN_ID)
    settlement.add_argument("--contract-address", required=True)
    settlement.add_argument("--job-json", required=True)
    settlement.add_argument("--round-json", required=True)
    settlement.add_argument("--attestation-hash", required=True)
    settlement.add_argument("--provider-payout-wei", type=int)
    settlement.add_argument("--requester-refund-wei", type=int)
    settlement.add_argument("--policy", default="success_90_10")
    settlement.set_defaults(func=_command_settlement)

    split = subparsers.add_parser("split")
    split.add_argument("--escrow-balance-wei", type=int, required=True)
    split.set_defaults(func=_command_split)

    onchain_job = subparsers.add_parser("onchain-job")
    onchain_job.add_argument("--rpc-url", required=True)
    onchain_job.add_argument("--contract-address", required=True)
    onchain_job.add_argument("--job-id", type=int, required=True)
    onchain_job.add_argument("--abi-path")
    onchain_job.set_defaults(func=_command_onchain_job)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
