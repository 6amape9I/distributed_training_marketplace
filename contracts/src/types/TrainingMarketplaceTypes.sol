// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

enum JobStatus {
    Open,
    Funded,
    Attested,
    Finalized
}

struct Job {
    address requester;
    address provider;
    address attestor;
    uint256 targetEscrow;
    uint256 escrowBalance;
    bytes32 jobSpecHash;
    bytes32 attestationHash;
    bytes32 settlementHash;
    uint256 providerPayout;
    uint256 requesterRefund;
    JobStatus status;
}
