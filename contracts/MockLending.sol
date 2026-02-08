// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IFlareCreditOracle {
    function getScore(address user) external view returns (
        uint256 tradFiScore,
        uint256 onChainScore,
        uint256 combinedRiskScore,
        uint256 maxBorrowAmount,
        uint256 recommendedAPR
    );
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract MockLending {
    struct Loan {
        uint256 amount;
        uint256 apr;
        uint256 timestamp;
        bool active;
    }

    IFlareCreditOracle public oracle;
    IERC20 public token; // The fake money (mUSDC) that gets lent out
    address public owner;
    mapping(address => bool) public agents;
    mapping(address => Loan) public loans;

    event LoanDisbursed(address indexed user, uint256 amount, uint256 apr);
    event LoanRepaid(address indexed user, uint256 amount);

    modifier onlyAgent() {
        require(agents[msg.sender] || msg.sender == owner, "Not authorized");
        _;
    }

    constructor(address oracleAddress, address tokenAddress) {
        oracle = IFlareCreditOracle(oracleAddress);
        token = IERC20(tokenAddress);
        owner = msg.sender;
        agents[msg.sender] = true;
    }

    function addAgent(address agent) external {
        require(msg.sender == owner, "Not owner");
        agents[agent] = true;
    }

    // Agent calls this after credit score is approved — sends fake money to user, no collateral
    function disburseLoan(address user, uint256 amount) external onlyAgent {
        (
            ,
            ,
            uint256 riskScore,
            uint256 maxBorrowAmount,
            uint256 apr
        ) = oracle.getScore(user);

        require(riskScore > 0, "No credit score on file");
        require(riskScore <= 60, "Credit risk too high");
        require(amount <= maxBorrowAmount, "Exceeds max borrow limit");
        require(!loans[user].active, "Already has active loan");
        require(token.balanceOf(address(this)) >= amount, "Lending pool insufficient");

        // Send the fake money to the user — no collateral needed!
        require(token.transfer(user, amount), "Transfer failed");

        loans[user] = Loan({
            amount: amount,
            apr: apr,
            timestamp: block.timestamp,
            active: true
        });

        emit LoanDisbursed(user, amount, apr);
    }

    // User repays their loan
    function repay() external {
        Loan storage loan = loans[msg.sender];
        require(loan.active, "No active loan");

        require(token.transferFrom(msg.sender, address(this), loan.amount), "Repay failed");

        loan.active = false;
        emit LoanRepaid(msg.sender, loan.amount);
    }

    // Check how much fake money is in the lending pool
    function poolBalance() external view returns (uint256) {
        return token.balanceOf(address(this));
    }
}
