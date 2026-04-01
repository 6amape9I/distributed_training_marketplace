// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Job} from "../types/TrainingMarketplaceTypes.sol";

interface ITrainingMarketplace {
    event JobCreated(
        uint256 indexed jobId,
        address indexed requester,
        address indexed provider,
        address attestor,
        uint256 targetEscrow,
        bytes32 jobSpecHash
    );
    event JobFunded(uint256 indexed jobId, address indexed funder, uint256 amount, uint256 escrowBalance);
    event JobFullyFunded(uint256 indexed jobId, uint256 escrowBalance);
    event AttestationSubmitted(uint256 indexed jobId, address indexed attestor, bytes32 attestationHash);
    event JobFinalized(
        uint256 indexed jobId,
        address indexed finalizer,
        uint256 providerPayout,
        uint256 requesterRefund,
        bytes32 settlementHash
    );
    event PayoutWithdrawn(uint256 indexed jobId, address indexed recipient, uint256 amount);
    event RefundWithdrawn(uint256 indexed jobId, address indexed recipient, uint256 amount);

    function createJob(address provider, address attestor, uint256 targetEscrow, bytes32 jobSpecHash)
        external
        returns (uint256 jobId);

    function fundJob(uint256 jobId) external payable;

    function submitAttestation(uint256 jobId, bytes32 attestationHash) external;

    function finalizeJob(uint256 jobId, uint256 providerPayout, uint256 requesterRefund, bytes32 settlementHash)
        external;

    function withdrawPayout(uint256 jobId) external;

    function withdrawRefund(uint256 jobId) external;

    function getJob(uint256 jobId) external view returns (Job memory job);
}
