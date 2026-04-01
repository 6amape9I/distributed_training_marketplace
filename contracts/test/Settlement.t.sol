// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {TrainingMarketplaceTestBase} from "./utils/TrainingMarketplaceTestBase.sol";
import {NothingToWithdraw, Unauthorized} from "../src/errors/TrainingMarketplaceErrors.sol";

contract SettlementTest is TrainingMarketplaceTestBase {
    function test_WithdrawPayoutTransfersEscrowShareToProvider() public {
        uint256 jobId = _createAttestedJob();
        vm.prank(attestor);
        marketplace.finalizeJob(jobId, TARGET_ESCROW, 0, SETTLEMENT_HASH);

        uint256 balanceBefore = provider.balance;
        vm.prank(provider);
        marketplace.withdrawPayout(jobId);

        assertEq(provider.balance, balanceBefore + TARGET_ESCROW);
        assertEq(marketplace.pendingPayouts(jobId), 0);
    }

    function test_WithdrawRefundTransfersEscrowShareToRequester() public {
        uint256 jobId = _createAttestedJob();
        vm.prank(attestor);
        marketplace.finalizeJob(jobId, 0, TARGET_ESCROW, SETTLEMENT_HASH);

        uint256 balanceBefore = requester.balance;
        vm.prank(requester);
        marketplace.withdrawRefund(jobId);

        assertEq(requester.balance, balanceBefore + TARGET_ESCROW);
        assertEq(marketplace.pendingRefunds(jobId), 0);
    }

    function test_WithdrawSupportsSplitSettlement() public {
        uint256 jobId = _createAttestedJob();
        vm.prank(attestor);
        marketplace.finalizeJob(jobId, 7 ether, 3 ether, SETTLEMENT_HASH);

        uint256 providerBefore = provider.balance;
        uint256 requesterBefore = requester.balance;

        vm.prank(provider);
        marketplace.withdrawPayout(jobId);
        vm.prank(requester);
        marketplace.withdrawRefund(jobId);

        assertEq(provider.balance, providerBefore + 7 ether);
        assertEq(requester.balance, requesterBefore + 3 ether);
    }

    function test_RevertWhen_DoublePayoutWithdrawal() public {
        uint256 jobId = _createAttestedJob();
        vm.prank(attestor);
        marketplace.finalizeJob(jobId, TARGET_ESCROW, 0, SETTLEMENT_HASH);

        vm.prank(provider);
        marketplace.withdrawPayout(jobId);

        vm.expectRevert(abi.encodeWithSelector(NothingToWithdraw.selector, jobId, provider));
        vm.prank(provider);
        marketplace.withdrawPayout(jobId);
    }

    function test_RevertWhen_UnauthorizedRefundWithdrawal() public {
        uint256 jobId = _createAttestedJob();
        vm.prank(attestor);
        marketplace.finalizeJob(jobId, 0, TARGET_ESCROW, SETTLEMENT_HASH);

        vm.expectRevert(abi.encodeWithSelector(Unauthorized.selector, outsider));
        vm.prank(outsider);
        marketplace.withdrawRefund(jobId);
    }
}
