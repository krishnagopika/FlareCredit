from pydantic import BaseModel
from typing import Optional, List

# Request Models
class ScoreRequest(BaseModel):
    user_address: str

class EvaluateLoanRequest(BaseModel):
    user_address: str
    requested_amount: float  # Amount in tokens (e.g., 500.0)

class DisburseRequest(BaseModel):
    user_address: str
    requested_amount: float  # Amount in tokens

# Response Models
class CreditScoreResponse(BaseModel):
    tradfi_score: int
    onchain_score: int
    combined_risk_score: int
    max_borrow_amount: str
    apr: float
    rng_jitter: Optional[int] = None
    flr_price_usd: Optional[float] = None
    xrp_price_usd: Optional[float] = None
    tx_hash: Optional[str] = None

class LoanStatusResponse(BaseModel):
    has_active_loan: bool
    user_address: str
    amount: Optional[str] = None
    amount_tokens: Optional[float] = None
    apr: Optional[float] = None
    borrowed_at: Optional[int] = None

class RepaymentInfoResponse(BaseModel):
    has_active_loan: bool
    user_address: str
    loan_info: Optional[dict] = None
    repayment: Optional[dict] = None
    user_status: Optional[dict] = None
    contract_addresses: Optional[dict] = None

class TransactionData(BaseModel):
    step: int
    type: str
    description: str
    to: str
    data: str
    value: str
    gas: str
    gasPrice: str
    nonce: str
    chainId: str

class PrepareRepaymentResponse(BaseModel):
    success: bool
    message: str
    repayment_amount: float
    transactions: List[TransactionData]
    instructions: List[str]

class HealthResponse(BaseModel):
    status: str
    blockchain_connected: bool
    agent_address: str

class EvaluateLoanResponse(BaseModel):
    approved: bool
    reason: Optional[str] = None
    requested_amount: Optional[str] = None
    max_borrow_amount: str
    utilization: Optional[str] = None
    base_apr: Optional[float] = None
    adjusted_apr: Optional[float] = None
    utilization_premium: Optional[float] = None
    loan_value_usd: Optional[float] = None
    flr_price_usd: Optional[float] = None
    xrp_price_usd: Optional[float] = None
    tx_hash: Optional[str] = None