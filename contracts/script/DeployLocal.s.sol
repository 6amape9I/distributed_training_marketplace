// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script} from "forge-std/Script.sol";
import {console2} from "forge-std/console2.sol";
import {TrainingMarketplace} from "../src/TrainingMarketplace.sol";

contract DeployLocalScript is Script {
    function run() external returns (TrainingMarketplace marketplace) {
        vm.startBroadcast();
        marketplace = new TrainingMarketplace();
        vm.stopBroadcast();

        console2.log("TrainingMarketplace deployed at", address(marketplace));
    }
}
