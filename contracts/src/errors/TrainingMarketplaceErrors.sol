// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {JobStatus} from "../types/TrainingMarketplaceTypes.sol";

error JobDoesNotExist(uint256 jobId);
error ZeroAddress();
error ZeroAmount();
error EmptyHash();
error InvalidTargetEscrow();
error Unauthorized(address caller);
error AttestationAlreadySubmitted(uint256 jobId);
error InvalidStatus(uint256 jobId, JobStatus expected, JobStatus actual);
error OverFunding(uint256 jobId, uint256 attemptedAmount, uint256 remainingAmount);
error InvalidSettlement(uint256 jobId, uint256 providerPayout, uint256 requesterRefund, uint256 escrowBalance);
error NothingToWithdraw(uint256 jobId, address recipient);
