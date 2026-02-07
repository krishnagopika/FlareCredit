// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

// This is the "fake money" users borrow (like USDC)
contract MockLoanToken is ERC20 {
    constructor() ERC20("Mock USDC", "mUSDC") {
        _mint(msg.sender, 1_000_000 * 10 ** decimals()); // 1M tokens
    }

    // Open mint so we can fund the lending pool anytime
    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}
