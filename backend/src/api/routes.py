from fastapi import APIRouter, HTTPException
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.utils.config import Config
from src.schemas.schemas import (
    ScoreRequest,
    EvaluateLoanRequest,
    CreditScoreResponse,
    DisburseRequest,
    LoanStatusResponse,
    RepaymentInfoResponse,
    HealthResponse,
    EvaluateLoanResponse
)

router = APIRouter()

# Will be injected from main.py
blockchain_service = None
tradfi_agent = None
onchain_agent = None
risk_agent = None
submission_agent = None

# ============================================================================
# HEALTH & INFO & DEBUG
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "blockchain_connected": blockchain_service.w3.is_connected(),
        "agent_address": blockchain_service.account.address
    }

@router.get("/credit-data/{user_address}")
async def mock_credit_data(user_address: str):
    """Mock credit data API — simulates Experian/Plaid responses per wallet."""
    seed = int(user_address[-8:], 16) % 1000
    fico = 550 + (seed % 270)
    return {
        "experian": {
            "fico_score": fico,
            "account_age_months": 12 + (seed % 168),
            "payment_history_percent": 70.0 + (seed % 30),
            "credit_utilization_percent": 5.0 + (seed % 80),
            "total_accounts": 2 + (seed % 23),
            "derogatory_marks": seed % 4,
            "total_debt": (seed % 50) * 1000,
        },
        "plaid": {
            "checking_balance": (seed % 250) * 100,
            "savings_balance": (seed % 500) * 100,
            "avg_monthly_income": 2000 + (seed % 130) * 100,
            "avg_monthly_expenses": 1500 + (seed % 105) * 100,
            "overdraft_count_6mo": seed % 6,
        },
        "payment_history": {
            "on_time_payments_12mo": 6 + (seed % 7),
            "late_payments_12mo": seed % 5,
            "missed_payments_12mo": seed % 3,
            "debt_to_income_ratio": round(0.1 + (seed % 10) * 0.1, 2),
        },
    }

# ============================================================================
# CREDIT SCORING
# ============================================================================

def _run_scoring_pipeline(user_address: str, requested_amount_wei: int = 0):
    """Shared pipeline: TradFi + OnChain in parallel → Risk → Submission."""
    state = {
        'user_address': user_address,
        'requested_amount': requested_amount_wei,
    }

    # TradFi and OnChain are independent — run in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        tradfi_future = executor.submit(tradfi_agent.fetch_data, dict(state))
        onchain_future = executor.submit(onchain_agent.analyze, dict(state))

        tradfi_state = tradfi_future.result()
        onchain_state = onchain_future.result()

    # Merge results into state
    state.update(tradfi_state)
    state.update(onchain_state)

    # Risk and submission must be sequential
    state = risk_agent.calculate_risk(state)
    state = submission_agent.submit(state)
    return state


@router.post("/process-score", response_model=CreditScoreResponse)
def process_score(request: ScoreRequest):
    """
    Run the credit scoring pipeline for a user and return their profile.
    No loan amount needed — just scores, FTSO prices, and on-chain submission.
    """
    try:
        state = _run_scoring_pipeline(request.user_address)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scoring pipeline failed: {e}")

    return CreditScoreResponse(
        tradfi_score=state['tradfi_score'],
        onchain_score=state['onchain_score'],
        combined_risk_score=state['combined_risk_score'],
        max_borrow_amount=str(state['max_borrow_amount']),
        apr=state['apr'] / 100,
        rng_jitter=state.get('rng_jitter'),
        flr_price_usd=state.get('flr_price_usd'),
        xrp_price_usd=state.get('xrp_price_usd'),
        tx_hash=state.get('tx_hash'),
    )


@router.post("/evaluate-loan", response_model=EvaluateLoanResponse)
def evaluate_loan(request: EvaluateLoanRequest):
    """
    Fast loan eligibility preview with agentic reasoning.
    Reads cached on-chain score + fresh balance check via RPC.
    Returns approved/denied with Gemini-generated explanation.
    """
    address = request.user_address
    requested_wei = int(request.requested_amount * 10**18)

    if request.requested_amount <= 0:
        return EvaluateLoanResponse(
            approved=False,
            reason="Requested amount must be greater than 0.",
            max_borrow_amount="0",
        )

    # 1. Check active loan
    has_loan = blockchain_service.check_active_loan(address)
    if has_loan:
        return EvaluateLoanResponse(
            approved=False,
            reason="User already has an active loan. Repay the existing loan before borrowing again.",
            max_borrow_amount="0",
            requested_amount=str(requested_wei),
        )

    # 2. Read cached on-chain score (from process-score)
    score = blockchain_service.get_user_score(address)
    if not score or score['combined_risk_score'] == 0:
        return EvaluateLoanResponse(
            approved=False,
            reason="No credit score found. Run /process-score first.",
            max_borrow_amount="0",
            requested_amount=str(requested_wei),
        )

    max_borrow = score['max_borrow_amount']
    base_apr = score['apr']
    risk = score['combined_risk_score']

    # 3. Fetch live FTSO prices for USD valuation
    ftso = blockchain_service.get_ftso_prices()
    flr_price = ftso['flr_usd'] if ftso else None
    xrp_price = ftso['xrp_usd'] if ftso else None
    loan_value_usd = (requested_wei / 10**18) * xrp_price if xrp_price else None

    # 4. Check risk ceiling
    MAX_ACCEPTABLE_RISK = 60
    if risk > MAX_ACCEPTABLE_RISK:
        return EvaluateLoanResponse(
            approved=False,
            reason=f"Credit risk score {risk}/100 exceeds the maximum acceptable threshold of {MAX_ACCEPTABLE_RISK}.",
            max_borrow_amount=str(max_borrow),
            requested_amount=str(requested_wei),
        )

    # 5. Check amount limit
    if requested_wei > max_borrow:
        return EvaluateLoanResponse(
            approved=False,
            reason=f"Requested {request.requested_amount:.0f} tokens exceeds max borrowing limit of {max_borrow / 10**18:.0f} tokens.",
            max_borrow_amount=str(max_borrow),
            requested_amount=str(requested_wei),
        )

    # 6. Check pool liquidity
    pool = blockchain_service.get_pool_balance()
    if pool and pool['balance_wei'] < requested_wei:
        return EvaluateLoanResponse(
            approved=False,
            reason=f"Insufficient pool liquidity. Available: {pool['balance_tokens']:.0f} tokens.",
            max_borrow_amount=str(max_borrow),
            requested_amount=str(requested_wei),
        )

    # 7. Calculate utilization-adjusted APR
    utilization = requested_wei / max_borrow if max_borrow > 0 else 0
    utilization_premium = int(utilization * 200)
    adjusted_apr = base_apr + utilization_premium

    # 8. Agentic reasoning via Claude
    reasoning = _get_loan_reasoning(score, request.requested_amount, utilization, adjusted_apr)

    return EvaluateLoanResponse(
        approved=True,
        reason=reasoning,
        requested_amount=str(requested_wei),
        max_borrow_amount=str(max_borrow),
        utilization=f"{utilization * 100:.1f}%",
        base_apr=base_apr / 100,
        adjusted_apr=adjusted_apr / 100,
        utilization_premium=utilization_premium / 100,
        loan_value_usd=loan_value_usd,
        flr_price_usd=flr_price,
        xrp_price_usd=xrp_price,
    )


def _get_loan_reasoning(score, requested_tokens, utilization, adjusted_apr_bps):
    """Use Claude to produce a human-readable loan approval explanation."""
    try:
        from langchain_aws import ChatBedrockConverse
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatBedrockConverse(
            model=Config.BEDROCK_MODEL_ID,
            region_name=Config.AWS_REGION,
            temperature=0.2,
        )

        messages = [
            SystemMessage(content=(
                "You are a DeFi lending advisor. Given the borrower's credit data and loan request, "
                "write a concise 2-3 sentence approval summary explaining why the loan is approved "
                "and any relevant notes about the terms. Be professional and factual. "
                "Return plain text only, no JSON or markdown."
            )),
            HumanMessage(content=(
                f"TradFi score: {score['tradfi_score']}/1000, "
                f"OnChain score: {score['onchain_score']}/100, "
                f"Risk score: {score['combined_risk_score']}/100, "
                f"Requested: {requested_tokens:.0f} tokens, "
                f"Max allowed: {score['max_borrow_amount'] / 10**18:.0f} tokens, "
                f"Utilization: {utilization * 100:.1f}%, "
                f"APR: {adjusted_apr_bps / 100:.2f}%"
            )),
        ]

        response = llm.invoke(messages)
        return response.content.strip()

    except Exception as e:
        print(f"[EvaluateLoan] Claude reasoning failed ({e}), using fallback")
        return _fallback_reasoning(score, requested_tokens, utilization, adjusted_apr_bps)


def _fallback_reasoning(score, requested_tokens, utilization, adjusted_apr_bps):
    """Rule-based fallback reasoning."""
    risk = score['combined_risk_score']
    if risk <= 20:
        tier = "excellent"
    elif risk <= 40:
        tier = "good"
    elif risk <= 60:
        tier = "fair"
    else:
        tier = "elevated"

    return (
        f"Loan approved. Borrower has {tier} credit profile "
        f"(risk {risk}/100, TradFi {score['tradfi_score']}/1000, OnChain {score['onchain_score']}/100). "
        f"Requesting {requested_tokens:.0f} of {score['max_borrow_amount'] / 10**18:.0f} max tokens "
        f"({utilization * 100:.1f}% utilization) at {adjusted_apr_bps / 100:.2f}% APR."
    )

# ============================================================================
# LOAN DISBURSEMENT
# ============================================================================

def _parse_revert_reason(error_msg: str) -> str:
    """Extract human-readable revert reason from contract error."""
    known_reasons = {
        "No credit score on file": "No credit score found on-chain. Please run credit scoring first.",
        "Credit risk too high": "Your credit risk score exceeds the acceptable threshold for borrowing.",
        "Exceeds max borrow limit": "Requested amount exceeds your maximum borrowing limit.",
        "Already has active loan": "You already have an active loan. Repay it before borrowing again.",
        "Lending pool insufficient": "The lending pool does not have enough liquidity for this loan.",
        "Not authorized": "The backend agent is not authorized to disburse loans.",
        "Transfer failed": "Token transfer failed during disbursement.",
    }
    for reason, friendly in known_reasons.items():
        if reason in str(error_msg):
            return friendly
    return f"Contract rejected the transaction: {error_msg}"


@router.post("/disburse-loan")
def disburse_loan(request: DisburseRequest):
    """
    Disburse loan to user.
    Backend does soft pre-flight checks for fast UX feedback.
    The smart contract enforces hard on-chain checks as the final authority.
    """
    address = request.user_address
    requested_wei = int(request.requested_amount * 10**18)

    if request.requested_amount <= 0:
        raise HTTPException(status_code=400, detail="Requested amount must be greater than 0")

    # --- Soft pre-flight checks (fast UX feedback, not authoritative) ---

    try:
        has_loan = blockchain_service.check_active_loan(address)
        if has_loan:
            raise HTTPException(status_code=400, detail="User already has an active loan. Repay it first.")
    except HTTPException:
        raise
    except Exception:
        pass  # Let the contract be the authority if RPC check fails

    try:
        score = blockchain_service.get_user_score(address)
        if not score or score['combined_risk_score'] == 0:
            raise HTTPException(status_code=404, detail="No credit score found. Run credit scoring first.")

        MAX_ACCEPTABLE_RISK = 60
        if score['combined_risk_score'] > MAX_ACCEPTABLE_RISK:
            raise HTTPException(
                status_code=400,
                detail=f"Credit risk too high ({score['combined_risk_score']}/100). Maximum acceptable is {MAX_ACCEPTABLE_RISK}."
            )

        if requested_wei > score['max_borrow_amount']:
            max_tokens = score['max_borrow_amount'] / 10**18
            raise HTTPException(
                status_code=400,
                detail=f"Requested {request.requested_amount:.0f} tokens exceeds your max borrow limit of {max_tokens:.0f} tokens."
            )
    except HTTPException:
        raise
    except Exception:
        pass  # Let the contract be the authority

    try:
        pool = blockchain_service.get_pool_balance()
        if pool and pool['balance_wei'] < requested_wei:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient pool liquidity. Available: {pool['balance_tokens']:.0f} tokens."
            )
    except HTTPException:
        raise
    except Exception:
        pass

    # --- On-chain disbursement (contract enforces all checks) ---
    try:
        result = blockchain_service.disburse_loan(address, requested_wei)

        if result is None:
            raise HTTPException(status_code=500, detail="Disbursement transaction returned no result.")

        if result['status'] != 1:
            raise HTTPException(status_code=500, detail="Transaction reverted on-chain.")

        return {
            "success": True,
            "message": "Loan disbursed successfully",
            "user_address": address,
            "amount_tokens": request.requested_amount,
            "amount_wei": str(requested_wei),
            "tx_hash": result['transactionHash'].hex(),
            "gas_used": result['gasUsed'],
        }

    except HTTPException:
        raise
    except Exception as e:
        detail = _parse_revert_reason(str(e))
        raise HTTPException(status_code=400, detail=detail)

# ============================================================================
# LOAN STATUS & REPAYMENT
# ============================================================================

@router.get("/loan-status/{user_address}", response_model=LoanStatusResponse)
def get_loan_status(user_address: str):
    """Get user's active loan status"""
    
    try:
        loan = blockchain_service.get_loan_info(user_address)
        
        if not loan or not loan['active']:
            return {
                "has_active_loan": False,
                "user_address": user_address
            }
        
        return {
            "has_active_loan": True,
            "user_address": user_address,
            "amount": str(loan['amount']),
            "amount_tokens": loan['amount'] / 10**18,
            "apr": loan['apr'] / 100,
            "borrowed_at": loan['timestamp']
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/repayment-info/{user_address}", response_model=RepaymentInfoResponse)
def get_repayment_info(user_address: str):
    """
    Get complete repayment information for a user.
    Includes loan details, repayment amount, user balance, and allowance.
    """
    try:
        # Check if user has active loan
        loan = blockchain_service.get_loan_info(user_address)
        
        if not loan or not loan['active']:
            return {
                "has_active_loan": False,
                "user_address": user_address
            }
        
        # Get repayment amount
        repayment = blockchain_service.get_repayment_amount(user_address)
        
        if not repayment:
            raise HTTPException(
                status_code=500,
                detail="Failed to calculate repayment amount"
            )
        
        # Get user's token balance
        user_balance = blockchain_service.get_user_token_balance(user_address)
        
        # Get allowance
        allowance = blockchain_service.get_token_allowance(
            user_address,
            blockchain_service.lending.address
        )
        
        return {
            "has_active_loan": True,
            "user_address": user_address,
            "loan_info": {
                "principal": loan['amount'] / 10**18,
                "principal_wei": str(loan['amount']),
                "apr": loan['apr'] / 100,
                "borrowed_at": loan['timestamp']
            },
            "repayment": {
                "total_amount": repayment['repayment_amount_tokens'],
                "total_amount_wei": str(repayment['repayment_amount_wei']),
                "interest": repayment.get('interest_tokens', 0),
                "time_elapsed_days": repayment.get('time_elapsed_days', 0)
            },
            "user_status": {
                "balance": user_balance['balance_tokens'],
                "balance_wei": str(user_balance['balance_wei']),
                "has_sufficient_balance": user_balance['balance_wei'] >= repayment['repayment_amount_wei'],
                "allowance": allowance['allowance_tokens'],
                "allowance_wei": str(allowance['allowance_wei']),
                "needs_approval": allowance['allowance_wei'] < repayment['repayment_amount_wei']
            },
            "contract_addresses": {
                "lending_contract": blockchain_service.lending.address,
                "token_contract": blockchain_service.token.address
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))