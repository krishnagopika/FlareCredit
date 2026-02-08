# FlareCredit

Uncollateralized DeFi lending powered by AI credit scoring and Flare's native data protocols. FlareCredit combines traditional finance credit data with on-chain activity analysis to enable trust-based borrowing without collateral.

## Built on Flare

**Network:** Flare Coston2 Testnet

**Integrations:**

- **Flare Data Connector (FDC)** — Fetches and attests external TradFi data via JsonApi attestation. Credit scores from bureaus (simulated Experian/TransUnion) and bank account data from aggregators (simulated Plaid) are brought on-chain with cryptographic integrity proofs.
- **Flare Time Series Oracle (FTSO v2)** — Live FLR/USD and XRP/USD price feeds for real-time USD valuation of wallet balances and loan amounts. Used during on-chain scoring and loan evaluation.
- **Flare Secure Random Number Generator (RandomNumberV2)** — Adds verifiable randomness jitter to credit scores, preventing deterministic gaming of the scoring algorithm.

## Smart Contracts (Coston2)

| Contract | Address | Description |
|----------|---------|-------------|
| **FlareCreditOracle** | [`0xa87209410af28367472073Cebf8cbac86c802Bb7`](https://coston2-explorer.flare.network/address/0xa87209410af28367472073Cebf8cbac86c802Bb7) | Stores AI-computed credit scores on-chain. Agents submit TradFi + on-chain scores; the lending contract reads them to authorize loans. |
| **MockLending** | [`0x9feF5655Ad38c61E6F662c5aED8174dcde2fd788`](https://coston2-explorer.flare.network/address/0x9feF5655Ad38c61E6F662c5aED8174dcde2fd788) | Uncollateralized lending pool. Enforces all checks on-chain: risk score threshold (<=60), borrow limits, active loan check, and pool liquidity. Disburses mUSDC directly to borrowers. |
| **MockLoanToken (mUSDC)** | [`0x45c7B48d002D014D0F8C8dff55045016AD28ACCB`](https://coston2-explorer.flare.network/address/0x45c7B48d002D014D0F8C8dff55045016AD28ACCB) | ERC-20 test stablecoin used as the lending currency. |

### Loan Disbursement Flow (On-Chain)

The `MockLending.disburseLoan()` function reads the user's credit score directly from the `FlareCreditOracle` contract and enforces all eligibility checks in a single atomic transaction:

1. Verifies a credit score exists (`riskScore > 0`)
2. Checks risk is acceptable (`riskScore <= 60`)
3. Validates amount is within the user's borrow limit
4. Confirms no existing active loan
5. Verifies pool has sufficient liquidity
6. Transfers mUSDC to the borrower

No off-chain trust is required — the contract is the final authority.

## User Journey

1. **Connect Wallet** — User connects via MetaMask on the landing page and is redirected to the dashboard.
2. **Analyze Credit Score** — User clicks "Analyze Credit Score", which triggers the multi-agent pipeline:
   - **TradFi Agent** fetches external credit data via Flare FDC (FICO, payment history, utilization)
   - **On-Chain Agent** analyzes wallet activity, balance (valued via FTSO), and transaction history
   - **Risk Agent** combines both scores with FTSO price data and secure random jitter
   - **Submission Agent** writes the final score on-chain to the FlareCreditOracle
3. **Review Credit Profile** — Dashboard displays TradFi score, on-chain score, combined risk score, max borrow amount, and expected APR.
4. **Apply for Loan** — User selects amount, token, and purpose. The backend checks eligibility against on-chain data and returns an AI-generated approval summary.
5. **Confirm Disbursement** — On approval, the backend calls `MockLending.disburseLoan()`, which enforces all checks on-chain and transfers mUSDC to the user's wallet.
6. **Repay Loan** — User expands the Loan Status card, reviews repayment details (principal + accrued interest), and clicks "Repay Loan" which triggers a 2-step MetaMask flow: ERC-20 approve + contract repay.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│   Next.js    │────>│  FastAPI Backend  │────>│   Flare Coston2     │
│   Frontend   │<────│  (AI Agents)      │<────│   Smart Contracts   │
└─────────────┘     └──────────────────┘     └─────────────────────┘
                           │                         │
                     ┌─────┴──────┐            ┌─────┴──────┐
                     │ Claude AI  │            │ FTSO v2    │
                     │ (Bedrock)  │            │ FDC        │
                     └────────────┘            │ RNG v2     │
                                               └────────────┘
```

- **Frontend:** Next.js 15 + wagmi + RainbowKit + Framer Motion
- **Backend:** FastAPI + LangGraph multi-agent system (Claude via AWS Bedrock)
- **Contracts:** Solidity 0.8.20, deployed via Hardhat 3

## AI Credit Scoring Pipeline

The backend runs a LangGraph-orchestrated multi-agent system powered by Claude (via AWS Bedrock) that evaluates creditworthiness in parallel before writing results on-chain.

| Agent | Role | Data Source |
|-------|------|-------------|
| **TradFi Agent** | Scores traditional credit factors (FICO from credit bureaus, account balances and payment history from Plaid, utilization, debt-to-income) | External APIs via Flare FDC |
| **On-Chain Agent** | Analyzes wallet age, transaction count, and native balance (USD-valued via FTSO) | Flare RPC + FTSO v2 |
| **Risk Agent** | Merges both scores into a combined risk profile, computes max borrow and APR, applies RNG jitter | Claude (Bedrock) + RandomNumberV2 |
| **Submission Agent** | Writes the final credit score on-chain to FlareCreditOracle | Flare smart contract tx |

TradFi and On-Chain agents run **in parallel** via a LangGraph graph, then feed into the sequential Risk and Submission agents. Each agent uses Claude Sonnet on AWS Bedrock for reasoning — interpreting raw data, weighing risk factors, and generating human-readable explanations for loan approvals.

## demo - recording

[recording](https://drive.google.com/file/d/1ye9MlVsAFXFMHBCOjoh5-YYZI0BCQeNT/view?usp=drive_link)

## Live Demo

| Service | URL |
|---------|-----|
| **Frontend** | [http://98.93.194.67:3000](http://98.93.194.67:3000) |
| **Backend API** | [http://98.93.194.67:8000/docs](http://98.93.194.67:8000/docs) |
| **Faucet API** | [http://98.93.194.67:8001/docs](http://98.93.194.67:8001/docs) |

**Getting Test Tokens:**
1. Use the Faucet API to mint mUSDC to your MetaMask account.
2. To see your mUSDC balance in MetaMask, import the token using contract address: `0x45c7B48d002D014D0F8C8dff55045016AD28ACCB`
## Setup

### Prerequisites

- Node.js 18+, Python 3.11+, MetaMask wallet
- AWS credentials with Bedrock access (Claude 4.5 Sonnnet)

### 1. Clone and install

```bash
git clone https://github.com/krishnagopika/FlareCredit.git
cd FlareCredit
npm install
```

### 2. Deploy contracts (or use existing Coston2 deployments)

```bash
cp .env.example .env
# Add your PRIVATE_KEY and RPC_URL
npx hardhat run scripts/deploy.js --network coston2
```

### 3. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in contract addresses, AWS credentials
python -m src.main
```

### 4. Frontend

```bash
cd flare-credit-ui
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and connect your wallet.

## Future Scope

- **FAssets Integration** — Replace mUSDC with FXRP, FBTC, and FDOGE as lending currencies, enabling real-asset-backed uncollateralized loans across multiple token types.
- **USDT0 Support** — Add native USDT0 stablecoin as a borrowing option for lower-volatility lending.
- **Multi-Currency Lending Pools** — Separate pools per asset with FTSO-powered dynamic interest rates that adjust based on real-time market conditions.
- **FDC Credit Bureau Attestation** — Connect to real credit bureaus (Experian, TransUnion) via FDC JsonApi for production-grade credit data instead of simulated sources.
- **On-Chain Credit History** — Build a portable, cross-protocol credit reputation from repayment behavior, usable across any Flare DeFi protocol.
- **Flare Mainnet Deployment** — Migrate from Coston2 testnet to Flare mainnet with audited contracts and production FDC attestation.

## Environment Variables

See `.env.example` at the repo root for all required variables.

## License

MIT
