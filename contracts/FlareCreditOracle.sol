// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract FlareCreditOracle {

    struct CreditScore {
        uint256 tradFiScore;       // 0-1000, mock FICO
        uint256 onChainScore;      // 0-100
        uint256 combinedRiskScore; // 0-100, lower = better
        uint256 maxBorrowAmount;   // max they can borrow (in token units)
        uint256 apr;               // basis points (500 = 5%)
        uint256 validUntil;        // expiry timestamp
    }

    address public owner;
    mapping(address => bool) public agents;
    mapping(address => CreditScore) public scores;

    event CreditScoreRequested(address indexed user);
    event CreditScoreSubmitted(address indexed user, uint256 combinedRiskScore, uint256 maxBorrowAmount);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAgent() {
        require(agents[msg.sender] || msg.sender == owner, "Not authorized agent");
        _;
    }

    constructor() {
        owner = msg.sender;
        agents[msg.sender] = true;
    }

    function addAgent(address agent) external onlyOwner {
        agents[agent] = true;
    }

    // User calls this to request a credit score — backend listens for the event
    function requestCreditScore() external {
        emit CreditScoreRequested(msg.sender);
    }

    // Agent submits the calculated score on-chain
    function submitCreditScore(
        address user,
        uint256 tradFiScore,
        uint256 onChainScore,
        uint256 combinedRiskScore,
        uint256 maxBorrowAmount,
        uint256 apr,
        uint256 validUntil
    ) external onlyAgent {
        scores[user] = CreditScore(
            tradFiScore,
            onChainScore,
            combinedRiskScore,
            maxBorrowAmount,
            apr,
            validUntil
        );
        emit CreditScoreSubmitted(user, combinedRiskScore, maxBorrowAmount);
    }

    function getScore(address user) external view returns (
        uint256 tradFiScore,
        uint256 onChainScore,
        uint256 combinedRiskScore,
        uint256 maxBorrowAmount,
        uint256 recommendedAPR
    ) {
        CreditScore memory s = scores[user];
        return (s.tradFiScore, s.onChainScore, s.combinedRiskScore, s.maxBorrowAmount, s.apr);
    }

    function getFullScore(address user) external view returns (CreditScore memory) {
        return scores[user];
    }
}
