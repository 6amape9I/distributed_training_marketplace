// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Address} from "@openzeppelin/contracts/utils/Address.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {ITrainingMarketplace} from "./interfaces/ITrainingMarketplace.sol";
import {Job, JobStatus} from "./types/TrainingMarketplaceTypes.sol";
import {
    AttestationAlreadySubmitted,
    EmptyHash,
    InvalidSettlement,
    InvalidStatus,
    InvalidTargetEscrow,
    JobDoesNotExist,
    NothingToWithdraw,
    OverFunding,
    Unauthorized,
    ZeroAddress,
    ZeroAmount
} from "./errors/TrainingMarketplaceErrors.sol";

contract TrainingMarketplace is ITrainingMarketplace, ReentrancyGuard {
    using Address for address payable;

    uint256 public nextJobId = 1;

    mapping(uint256 jobId => Job job) private jobs;
    mapping(uint256 jobId => uint256 amount) public pendingPayouts;
    mapping(uint256 jobId => uint256 amount) public pendingRefunds;

    function createJob(address provider, address attestor, uint256 targetEscrow, bytes32 jobSpecHash)
        external
        returns (uint256 jobId)
    {
        if (provider == address(0) || attestor == address(0)) {
            revert ZeroAddress();
        }
        if (targetEscrow == 0) {
            revert InvalidTargetEscrow();
        }
        if (jobSpecHash == bytes32(0)) {
            revert EmptyHash();
        }

        jobId = nextJobId;
        nextJobId += 1;

        jobs[jobId] = Job({
            requester: msg.sender,
            provider: provider,
            attestor: attestor,
            targetEscrow: targetEscrow,
            escrowBalance: 0,
            jobSpecHash: jobSpecHash,
            attestationHash: bytes32(0),
            settlementHash: bytes32(0),
            providerPayout: 0,
            requesterRefund: 0,
            status: JobStatus.Open
        });

        emit JobCreated(jobId, msg.sender, provider, attestor, targetEscrow, jobSpecHash);
    }

    function fundJob(uint256 jobId) external payable {
        Job storage job = _getExistingJob(jobId);
        _requireCaller(job.requester);
        _requireStatus(jobId, job.status, JobStatus.Open);

        if (msg.value == 0) {
            revert ZeroAmount();
        }

        uint256 remainingAmount = job.targetEscrow - job.escrowBalance;
        if (msg.value > remainingAmount) {
            revert OverFunding(jobId, msg.value, remainingAmount);
        }

        job.escrowBalance += msg.value;
        emit JobFunded(jobId, msg.sender, msg.value, job.escrowBalance);

        if (job.escrowBalance == job.targetEscrow) {
            job.status = JobStatus.Funded;
            emit JobFullyFunded(jobId, job.escrowBalance);
        }
    }

    function submitAttestation(uint256 jobId, bytes32 attestationHash) external {
        Job storage job = _getExistingJob(jobId);
        _requireCaller(job.attestor);

        if (attestationHash == bytes32(0)) {
            revert EmptyHash();
        }
        if (job.attestationHash != bytes32(0)) {
            revert AttestationAlreadySubmitted(jobId);
        }
        _requireStatus(jobId, job.status, JobStatus.Funded);

        job.attestationHash = attestationHash;
        job.status = JobStatus.Attested;

        emit AttestationSubmitted(jobId, msg.sender, attestationHash);
    }

    function finalizeJob(uint256 jobId, uint256 providerPayout, uint256 requesterRefund, bytes32 settlementHash)
        external
    {
        Job storage job = _getExistingJob(jobId);
        _requireCaller(job.attestor);
        _requireStatus(jobId, job.status, JobStatus.Attested);

        if (settlementHash == bytes32(0)) {
            revert EmptyHash();
        }
        if (providerPayout + requesterRefund != job.escrowBalance) {
            revert InvalidSettlement(jobId, providerPayout, requesterRefund, job.escrowBalance);
        }

        job.providerPayout = providerPayout;
        job.requesterRefund = requesterRefund;
        job.settlementHash = settlementHash;
        job.status = JobStatus.Finalized;

        pendingPayouts[jobId] = providerPayout;
        pendingRefunds[jobId] = requesterRefund;

        emit JobFinalized(jobId, msg.sender, providerPayout, requesterRefund, settlementHash);
    }

    function withdrawPayout(uint256 jobId) external nonReentrant {
        Job storage job = _getExistingJob(jobId);
        _requireCaller(job.provider);
        _requireStatus(jobId, job.status, JobStatus.Finalized);

        uint256 amount = pendingPayouts[jobId];
        if (amount == 0) {
            revert NothingToWithdraw(jobId, msg.sender);
        }

        pendingPayouts[jobId] = 0;
        payable(msg.sender).sendValue(amount);

        emit PayoutWithdrawn(jobId, msg.sender, amount);
    }

    function withdrawRefund(uint256 jobId) external nonReentrant {
        Job storage job = _getExistingJob(jobId);
        _requireCaller(job.requester);
        _requireStatus(jobId, job.status, JobStatus.Finalized);

        uint256 amount = pendingRefunds[jobId];
        if (amount == 0) {
            revert NothingToWithdraw(jobId, msg.sender);
        }

        pendingRefunds[jobId] = 0;
        payable(msg.sender).sendValue(amount);

        emit RefundWithdrawn(jobId, msg.sender, amount);
    }

    function getJob(uint256 jobId) external view returns (Job memory job) {
        job = _getExistingJob(jobId);
    }

    function _getExistingJob(uint256 jobId) internal view returns (Job storage job) {
        job = jobs[jobId];
        if (job.requester == address(0)) {
            revert JobDoesNotExist(jobId);
        }
    }

    function _requireCaller(address expectedCaller) internal view {
        if (msg.sender != expectedCaller) {
            revert Unauthorized(msg.sender);
        }
    }

    function _requireStatus(uint256 jobId, JobStatus actualStatus, JobStatus expectedStatus) internal pure {
        if (actualStatus != expectedStatus) {
            revert InvalidStatus(jobId, expectedStatus, actualStatus);
        }
    }
}
