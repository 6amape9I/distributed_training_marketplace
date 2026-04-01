// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {TrainingMarketplaceTestBase} from "./utils/TrainingMarketplaceTestBase.sol";
import {Job, JobStatus} from "../src/types/TrainingMarketplaceTypes.sol";
import {
    AttestationAlreadySubmitted,
    InvalidSettlement,
    InvalidStatus,
    Unauthorized
} from "../src/errors/TrainingMarketplaceErrors.sol";

contract JobLifecycleTest is TrainingMarketplaceTestBase {
    function test_SubmitAttestationMovesJobToAttested() public {
        uint256 jobId = _createFundedJob();

        vm.prank(attestor);
        marketplace.submitAttestation(jobId, ATTESTATION_HASH);

        Job memory job = marketplace.getJob(jobId);
        assertEq(job.attestationHash, ATTESTATION_HASH);
        assertEq(uint256(job.status), uint256(JobStatus.Attested));
    }

    function test_FinalizeJobStoresSettlementAndTransitionsStatus() public {
        uint256 jobId = _createAttestedJob();

        vm.prank(attestor);
        marketplace.finalizeJob(jobId, 8 ether, 2 ether, SETTLEMENT_HASH);

        Job memory job = marketplace.getJob(jobId);
        assertEq(job.providerPayout, 8 ether);
        assertEq(job.requesterRefund, 2 ether);
        assertEq(job.settlementHash, SETTLEMENT_HASH);
        assertEq(uint256(job.status), uint256(JobStatus.Finalized));
        assertEq(marketplace.pendingPayouts(jobId), 8 ether);
        assertEq(marketplace.pendingRefunds(jobId), 2 ether);
    }

    function test_RevertWhen_AttestationSubmittedByNonAttestor() public {
        uint256 jobId = _createFundedJob();

        vm.expectRevert(abi.encodeWithSelector(Unauthorized.selector, outsider));
        vm.prank(outsider);
        marketplace.submitAttestation(jobId, ATTESTATION_HASH);
    }

    function test_RevertWhen_FinalizeBeforeAttestation() public {
        uint256 jobId = _createFundedJob();

        vm.expectRevert(abi.encodeWithSelector(InvalidStatus.selector, jobId, JobStatus.Attested, JobStatus.Funded));
        vm.prank(attestor);
        marketplace.finalizeJob(jobId, TARGET_ESCROW, 0, SETTLEMENT_HASH);
    }

    function test_RevertWhen_FinalizeSettlementDoesNotMatchEscrow() public {
        uint256 jobId = _createAttestedJob();

        vm.expectRevert(abi.encodeWithSelector(InvalidSettlement.selector, jobId, 9 ether, 2 ether, TARGET_ESCROW));
        vm.prank(attestor);
        marketplace.finalizeJob(jobId, 9 ether, 2 ether, SETTLEMENT_HASH);
    }

    function test_RevertWhen_AttestationIsSubmittedTwice() public {
        uint256 jobId = _createAttestedJob();

        vm.expectRevert(abi.encodeWithSelector(AttestationAlreadySubmitted.selector, jobId));
        vm.prank(attestor);
        marketplace.submitAttestation(jobId, ATTESTATION_HASH);
    }

    function test_RevertWhen_DoubleFinalize() public {
        uint256 jobId = _createAttestedJob();

        vm.prank(attestor);
        marketplace.finalizeJob(jobId, TARGET_ESCROW, 0, SETTLEMENT_HASH);

        vm.expectRevert(abi.encodeWithSelector(InvalidStatus.selector, jobId, JobStatus.Attested, JobStatus.Finalized));
        vm.prank(attestor);
        marketplace.finalizeJob(jobId, TARGET_ESCROW, 0, SETTLEMENT_HASH);
    }
}
