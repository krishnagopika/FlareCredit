from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
from src.schemas.schemas import (
    CreditScoreRequest,
    CreditScoreResponse,
    DisburseRequest,
    LoanStatusResponse,
    RepaymentInfoResponse,
    PrepareRepaymentResponse,
    TransactionData,
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

def process_credit_request_background(user_address: str, requested_amount: int = 0):
    """Background task to process credit score"""
    
    print(f"\nProcessing credit score for: {user_address}")
    if requested_amount > 0:
        print(f"Requested loan amount: {requested_amount / 10**18:.0f} tokens")
    print(f"{'='*60}\n")
    
    state = {
        'user_address': user_address,
        'requested_amount': requested_amount
    }
    
    try:
        # Run through agents
        state = tradfi_agent.fetch_data(state)
        state = onchain_agent.analyze(state)
        state = risk_agent.calculate_risk(state)
        state = submission_agent.submit(state)
        
        print(f"\n{'='*60}")
        print("COMPLETED")
        print(f"Transaction: {state['tx_hash']}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()

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

@router.get("/onchain-data/{user_address}")
async def get_onchain_data(user_address: str):
    """Get raw on-chain data for a user"""
    try:
        data = blockchain_service.get_onchain_data(user_address)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/contract-functions")
async def get_contract_functions():
    """List all available functions in the lending contract"""
    
    functions = []
    for item in blockchain_service.lending.abi:
        if item.get('type') == 'function':
            functions.append({
                'name': item['name'],
                'inputs': [
                    {
                        'name': inp.get('name', ''),
                        'type': inp.get('type', '')
                    } 
                    for inp in item.get('inputs', [])
                ],
                'outputs': [
                    {
                        'name': out.get('name', ''),
                        'type': out.get('type', '')
                    } 
                    for out in item.get('outputs', [])
                ],
                'stateMutability': item.get('stateMutability', '')
            })
    
    return {
        "lending_contract": blockchain_service.lending.address,
        "total_functions": len(functions),
        "functions": sorted(functions, key=lambda x: x['name'])
    }

# ============================================================================
# CREDIT SCORING
# ============================================================================

@router.post("/process-score", response_model=dict)
async def trigger_score_processing(
    request: CreditScoreRequest,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger credit score processing for a user.
    Optionally include requested loan amount for APR adjustment.
    """
    # Convert tokens to wei
    requested_wei = int(request.requested_amount * 10**18) if request.requested_amount > 0 else 0
    
    background_tasks.add_task(
        process_credit_request_background,
        request.user_address,
        requested_wei
    )
    
    return {
        "message": "Credit score processing started",
        "user_address": request.user_address,
        "requested_amount": request.requested_amount
    }

@router.get("/score/{user_address}", response_model=CreditScoreResponse)
async def get_credit_score(user_address: str):
    """Get existing credit score for a user from blockchain"""
    
    score = blockchain_service.get_user_score(user_address)
    
    if not score or score['combined_risk_score'] == 0:
        raise HTTPException(
            status_code=404,
            detail="No credit score found for this address"
        )
    
    return CreditScoreResponse(
        tradfi_score=score['tradfi_score'],
        onchain_score=score['onchain_score'],
        combined_risk_score=score['combined_risk_score'],
        max_borrow_amount=str(score['max_borrow_amount']),
        apr=score['apr'] / 100
    )

@router.post("/evaluate-loan", response_model=EvaluateLoanResponse)
async def evaluate_loan_request(request: CreditScoreRequest):
    """
    Evaluate a specific loan amount against user's credit score.
    Returns whether approved and adjusted APR.
    """
    score = blockchain_service.get_user_score(request.user_address)
    
    if not score or score['combined_risk_score'] == 0:
        raise HTTPException(
            status_code=404,
            detail="No credit score found. Please request a credit score first."
        )
    
    max_borrow = score['max_borrow_amount']
    base_apr = score['apr']
    requested_wei = int(request.requested_amount * 10**18)
    
    if requested_wei > max_borrow:
        return {
            "approved": False,
            "reason": "Requested amount exceeds maximum borrowing limit",
            "max_borrow_amount": str(max_borrow),
            "requested_amount": str(requested_wei)
        }
    
    # Calculate utilization-adjusted APR
    utilization = requested_wei / max_borrow if max_borrow > 0 else 0
    utilization_premium = int(utilization * 200)  # 0-200 basis points
    adjusted_apr = base_apr + utilization_premium
    
    return {
        "approved": True,
        "requested_amount": str(requested_wei),
        "max_borrow_amount": str(max_borrow),
        "utilization": f"{utilization * 100:.1f}%",
        "base_apr": base_apr / 100,
        "adjusted_apr": adjusted_apr / 100,
        "utilization_premium": utilization_premium / 100
    }

# ============================================================================
# LOAN DISBURSEMENT
# ============================================================================

@router.post("/disburse-loan")
async def disburse_loan(request: DisburseRequest):
    """
    Disburse approved loan to user.
    WARNING: This should be protected with authentication in production.
    """
    
    # Get user's credit score
    score = blockchain_service.get_user_score(request.user_address)
    
    if not score or score['combined_risk_score'] == 0:
        raise HTTPException(
            status_code=404,
            detail="No credit score found. User must request credit score first."
        )
    
    # Convert tokens to wei
    requested_wei = int(request.requested_amount * 10**18)
    max_borrow = score['max_borrow_amount']
    
    if request.requested_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Requested amount must be greater than 0"
        )
    
    if requested_wei > max_borrow:
        raise HTTPException(
            status_code=400,
            detail=f"Requested amount {request.requested_amount} mUSDC exceeds max borrow limit {max_borrow / 10**18} mUSDC"
        )
    
    # Check risk score
    MAX_ACCEPTABLE_RISK = 70
    if score['combined_risk_score'] > MAX_ACCEPTABLE_RISK:
        raise HTTPException(
            status_code=400,
            detail=f"Credit risk too high: {score['combined_risk_score']} (max acceptable: {MAX_ACCEPTABLE_RISK})"
        )
    
    # Check if user already has active loan
    has_loan = blockchain_service.check_active_loan(request.user_address)
    if has_loan:
        raise HTTPException(
            status_code=400,
            detail="User already has an active loan"
        )
    
    try:
        result = blockchain_service.disburse_loan(request.user_address, requested_wei)
        
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Insufficient pool balance"
            )
        
        if result['status'] != 1:
            raise HTTPException(
                status_code=500,
                detail=f"Transaction failed on-chain"
            )
        
        return {
            "success": True,
            "message": "Loan disbursed successfully",
            "user_address": request.user_address,
            "amount_tokens": request.requested_amount,
            "amount_wei": str(requested_wei),
            "tx_hash": result['transactionHash'].hex(),
            "gas_used": result['gasUsed']
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to disburse loan: {str(e)}"
        )

# ============================================================================
# LOAN STATUS & REPAYMENT
# ============================================================================

@router.get("/loan-status/{user_address}", response_model=LoanStatusResponse)
async def get_loan_status(user_address: str):
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
async def get_repayment_info(user_address: str):
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
@router.post("/prepare-repayment/{user_address}", response_model=PrepareRepaymentResponse)
async def prepare_repayment(user_address: str):
    """
    Prepare unsigned transaction data for loan repayment.
    User must sign and broadcast these transactions from their wallet.
    
    Returns:
    - Approval transaction (if needed)
    - Repayment transaction
    """
    try:
        # Get repayment info
        repayment_info = await get_repayment_info(user_address)
        
        if not repayment_info['has_active_loan']:
            raise HTTPException(
                status_code=404,
                detail="No active loan found for this address"
            )
        
        repayment_amount_wei = int(repayment_info['repayment']['total_amount_wei'])
        needs_approval = repayment_info['user_status']['needs_approval']
        
        transactions = []
        
        # Step 1: Approval transaction (if needed)
        if needs_approval:
            approve_tx = blockchain_service.token.functions.approve(
                blockchain_service.lending.address,
                repayment_amount_wei
            ).build_transaction({
                'from': user_address,
                'nonce': blockchain_service.w3.eth.get_transaction_count(user_address),
                'gas': 100000,
                'gasPrice': blockchain_service.w3.eth.gas_price,
                'chainId': 114  # Coston2
            })
            
            transactions.append(TransactionData(
                step=1,
                type='approve',
                description=f'Approve {repayment_amount_wei / 10**18:.2f} mUSDC for repayment',
                to=blockchain_service.token.address,
                data=approve_tx['data'],
                value='0x0',
                gas=hex(approve_tx['gas']),
                gasPrice=hex(approve_tx['gasPrice']),
                nonce=hex(approve_tx['nonce']),
                chainId='0x72'
            ))
        
        # Step 2: Repayment transaction using repay()
        repay_nonce = blockchain_service.w3.eth.get_transaction_count(user_address)
        if needs_approval:
            repay_nonce += 1  # Increment nonce after approval
            
        repay_tx = blockchain_service.lending.functions.repay().build_transaction({
            'from': user_address,
            'nonce': repay_nonce,
            'gas': 300000,
            'gasPrice': blockchain_service.w3.eth.gas_price,
            'chainId': 114
        })
        
        transactions.append(TransactionData(
            step=len(transactions) + 1,
            type='repay',
            description=f'Repay loan: {repayment_amount_wei / 10**18:.2f} mUSDC',
            to=blockchain_service.lending.address,
            data=repay_tx['data'],
            value='0x0',
            gas=hex(repay_tx['gas']),
            gasPrice=hex(repay_tx['gasPrice']),
            nonce=hex(repay_tx['nonce']),
            chainId='0x72'
        ))
        
        return PrepareRepaymentResponse(
            success=True,
            message='Transaction data prepared. User must sign and broadcast.',
            repayment_amount=repayment_amount_wei / 10**18,
            transactions=transactions,
            instructions=[
                'Connect your wallet (MetaMask, WalletConnect, etc.)',
                'Sign and broadcast these transactions in order:',
                '1. Approve mUSDC spending (if needed)',
                '2. Call repay() to complete repayment',
                'Tokens will be transferred from your wallet to the lending pool'
            ]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))