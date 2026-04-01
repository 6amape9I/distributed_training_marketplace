// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {TrainingMarketplace} from "../../src/TrainingMarketplace.sol";
import {JobStatus} from "../../src/types/TrainingMarketplaceTypes.sol";

abstract contract TrainingMarketplaceTestBase is Test {
    TrainingMarketplace internal marketplace;

    address internal requester = makeAddr("requester");
    address internal provider = makeAddr("provider");
    address internal attestor = makeAddr("attestor");
    address internal outsider = makeAddr("outsider");

    uint256 internal constant TARGET_ESCROW = 10 ether;
    bytes32 internal constant JOB_SPEC_HASH = keccak256("job-spec");
    bytes32 internal constant ATTESTATION_HASH = keccak256("attestation");
    bytes32 internal constant SETTLEMENT_HASH = keccak256("settlement");

    function setUp() public virtual {
        marketplace = new TrainingMarketplace();
        vm.deal(requester, 100 ether);
        vm.deal(provider, 1 ether);
        vm.deal(attestor, 1 ether);
        vm.deal(outsider, 1 ether);
    }

    function _createJob() internal returns (uint256 jobId) {
        vm.prank(requester);
        jobId = marketplace.createJob(provider, attestor, TARGET_ESCROW, JOB_SPEC_HASH);
    }

    function _fundJob(uint256 jobId, uint256 amount) internal {
        vm.prank(requester);
        marketplace.fundJob{value: amount}(jobId);
    }

    function _createFundedJob() internal returns (uint256 jobId) {
        jobId = _createJob();
        _fundJob(jobId, TARGET_ESCROW);
    }

    function _createAttestedJob() internal returns (uint256 jobId) {
        jobId = _createFundedJob();
        vm.prank(attestor);
        marketplace.submitAttestation(jobId, ATTESTATION_HASH);
    }

    function _jobStatus(uint256 jobId) internal view returns (JobStatus) {
        return marketplace.getJob(jobId).status;
    }
}
