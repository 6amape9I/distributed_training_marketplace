// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {TrainingMarketplaceTestBase} from "./utils/TrainingMarketplaceTestBase.sol";
import {Job, JobStatus} from "../src/types/TrainingMarketplaceTypes.sol";
import {EmptyHash, OverFunding, Unauthorized, ZeroAddress} from "../src/errors/TrainingMarketplaceErrors.sol";

contract TrainingMarketplaceCreationTest is TrainingMarketplaceTestBase {
    function test_CreateJobInitializesGenericLifecycleData() public {
        uint256 jobId = _createJob();
        assertEq(jobId, 1);

        Job memory job = marketplace.getJob(jobId);
        assertEq(job.requester, requester);
        assertEq(job.provider, provider);
        assertEq(job.attestor, attestor);
        assertEq(job.targetEscrow, TARGET_ESCROW);
        assertEq(job.jobSpecHash, JOB_SPEC_HASH);
        assertEq(uint256(job.status), uint256(JobStatus.Open));
    }

    function test_FundJobAllowsPartialFundingUntilTargetEscrow() public {
        uint256 jobId = _createJob();

        _fundJob(jobId, 4 ether);
        assertEq(uint256(_jobStatus(jobId)), uint256(JobStatus.Open));
        assertEq(marketplace.getJob(jobId).escrowBalance, 4 ether);

        _fundJob(jobId, 6 ether);
        assertEq(uint256(_jobStatus(jobId)), uint256(JobStatus.Funded));
        assertEq(marketplace.getJob(jobId).escrowBalance, TARGET_ESCROW);
    }

    function test_RevertWhen_CreateJobUsesZeroAddress() public {
        vm.expectRevert(abi.encodeWithSelector(ZeroAddress.selector));
        vm.prank(requester);
        marketplace.createJob(address(0), attestor, TARGET_ESCROW, JOB_SPEC_HASH);
    }

    function test_RevertWhen_CreateJobUsesEmptyJobSpecHash() public {
        vm.expectRevert(abi.encodeWithSelector(EmptyHash.selector));
        vm.prank(requester);
        marketplace.createJob(provider, attestor, TARGET_ESCROW, bytes32(0));
    }

    function test_RevertWhen_NonRequesterFundsJob() public {
        uint256 jobId = _createJob();

        vm.expectRevert(abi.encodeWithSelector(Unauthorized.selector, outsider));
        vm.prank(outsider);
        marketplace.fundJob{value: 1 ether}(jobId);
    }

    function test_RevertWhen_FundingExceedsTargetEscrow() public {
        uint256 jobId = _createJob();
        _fundJob(jobId, 9 ether);

        vm.expectRevert(abi.encodeWithSelector(OverFunding.selector, jobId, 2 ether, 1 ether));
        vm.prank(requester);
        marketplace.fundJob{value: 2 ether}(jobId);
    }
}
