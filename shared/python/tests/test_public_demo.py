from __future__ import annotations

from shared.python.public_demo import (
    build_attestation_artifact,
    build_settlement_artifact,
    compute_success_split,
)


def _job() -> dict[str, object]:
    return {
        "job_id": 1,
        "job_spec_hash": "0x" + "1" * 64,
        "requester": "0x00000000000000000000000000000000000000a1",
        "provider": "0x00000000000000000000000000000000000000b2",
        "attestor": "0x00000000000000000000000000000000000000c3",
        "offchain_status": "ready_for_attestation",
        "escrow_balance_wei": 10_000_000_000_000_000,
    }


def _round() -> dict[str, object]:
    return {
        "round_id": "round-1",
        "round_index": 1,
        "aggregated_model_artifact_uri": "artifact://aggregated-model",
        "aggregated_model_artifact_hash": "abc123",
        "evaluation_report_id": "evaluation-report-1",
    }


def _evaluation() -> dict[str, object]:
    return {
        "evaluation_task_id": "evaluation-task-1",
        "report_artifact_uri": "artifact://evaluation-report",
        "report_artifact_hash": "deadbeef",
    }


def test_attestation_hash_is_deterministic() -> None:
    first = build_attestation_artifact(
        network="base-sepolia",
        chain_id=84532,
        contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        job=_job(),
        round_record=_round(),
        evaluation_task=_evaluation(),
    )
    second = build_attestation_artifact(
        network="base-sepolia",
        chain_id=84532,
        contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        job=dict(reversed(list(_job().items()))),
        round_record=dict(reversed(list(_round().items()))),
        evaluation_task=dict(reversed(list(_evaluation().items()))),
    )

    assert first["canonical_json"] == second["canonical_json"]
    assert first["hash"] == second["hash"]


def test_success_split_uses_90_10_policy() -> None:
    provider_payout_wei, requester_refund_wei = compute_success_split(10_000_000_000_000_000)

    assert provider_payout_wei == 9_000_000_000_000_000
    assert requester_refund_wei == 1_000_000_000_000_000
    assert provider_payout_wei + requester_refund_wei == 10_000_000_000_000_000


def test_settlement_hash_is_deterministic() -> None:
    artifact = build_settlement_artifact(
        network="base-sepolia",
        chain_id=84532,
        contract_address="0x5FbDB2315678afecb367f032d93F642f64180aa3",
        job=_job(),
        round_record=_round(),
        attestation_hash="0x" + "2" * 64,
        provider_payout_wei=9_000_000_000_000_000,
        requester_refund_wei=1_000_000_000_000_000,
    )

    assert artifact["hash"].startswith("0x")
    assert artifact["payload"]["policy"] == "success_90_10"
    assert artifact["payload"]["provider_payout_wei"] == 9_000_000_000_000_000
    assert artifact["payload"]["requester_refund_wei"] == 1_000_000_000_000_000
