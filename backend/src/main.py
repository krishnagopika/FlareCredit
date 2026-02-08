from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
from contextlib import asynccontextmanager

from concurrent.futures import ThreadPoolExecutor
from src.services.blockchain_service import BlockchainService
from src.services.fdc_service import FlareFDCService
from src.agents.tradfi_agent import TradFiAgent
from src.agents.onchain_agent import OnChainAgent
from src.agents.risk_agent import RiskAgent
from src.agents.submission_agent import SubmissionAgent
from src.api import routes
from src.utils.config import Config

# Global instances
blockchain_service = None
fdc_service = None
tradfi_agent = None
onchain_agent = None
risk_agent = None
submission_agent = None

def process_credit_request(user_address: str, requested_amount: int = 0):
    """Process a credit score request through the agent pipeline"""

    print(f"\nProcessing credit score for: {user_address}")
    if requested_amount > 0:
        print(f"Requested amount: {requested_amount / 10**18:.0f} tokens")
    print(f"{'='*60}\n")

    state = {
        'user_address': user_address,
        'requested_amount': requested_amount
    }

    try:
        # TradFi and OnChain are independent — run in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            tradfi_future = executor.submit(tradfi_agent.fetch_data, dict(state))
            onchain_future = executor.submit(onchain_agent.analyze, dict(state))
            tradfi_state = tradfi_future.result()
            onchain_state = onchain_future.result()
        state.update(tradfi_state)
        state.update(onchain_state)

        state = risk_agent.calculate_risk(state)
        state = submission_agent.submit(state)

        print(f"\n{'='*60}")
        print("FINAL RESULTS:")
        print(f"{'='*60}")
        print(f"TradFi Score: {state['tradfi_score']}/1000")
        print(f"OnChain Score: {state['onchain_score']}/100")
        print(f"Combined Risk: {state['combined_risk_score']}/100")
        print(f"Max Borrow: {state['max_borrow_amount'] / 10**18:.0f} tokens")

        if requested_amount > 0:
            print(f"Requested: {requested_amount / 10**18:.0f} tokens")
            print(f"Approved: {state['approved_amount'] / 10**18:.0f} tokens")

        print(f"APR: {state['apr'] / 100}%")
        print(f"Transaction: {state['tx_hash']}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"Error processing request: {e}")
        import traceback
        traceback.print_exc()

def start_event_listener():
    """Start blockchain event listener in background thread"""
    blockchain_service.listen_for_score_requests(
        lambda user_address: process_credit_request(user_address, 0)
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""

    # Startup
    global blockchain_service, fdc_service, tradfi_agent, onchain_agent, risk_agent, submission_agent

    print("Flare Credit Agent System Starting...")

    # Validate config
    Config.validate()

    # Initialize services
    blockchain_service = BlockchainService()

    # Initialize Flare FDC service (Coston2 testnet)
    fdc_service = FlareFDCService(
        jq_verifier_url=Config.FDC_JQ_VERIFIER_URL,
        da_layer_url=Config.FDC_DA_LAYER_URL,
        data_api_url=Config.FDC_DATA_API_URL,
        fdc_hub_address=Config.FDC_HUB_ADDRESS,
        fdc_verification_address=Config.FDC_VERIFICATION_ADDRESS,
        fdc_fee_address=Config.FDC_FEE_ADDRESS,
        w3=blockchain_service.w3,
        api_key=Config.FDC_API_KEY or None,
    )

    # Initialize agents (TradFi now uses FDC for external data)
    tradfi_agent = TradFiAgent(fdc_service)
    onchain_agent = OnChainAgent(blockchain_service)
    risk_agent = RiskAgent(blockchain_service)
    submission_agent = SubmissionAgent(blockchain_service)

    # Inject into routes
    routes.blockchain_service = blockchain_service
    routes.tradfi_agent = tradfi_agent
    routes.onchain_agent = onchain_agent
    routes.risk_agent = risk_agent
    routes.submission_agent = submission_agent

    # Start event listener in background thread
    listener_thread = threading.Thread(target=start_event_listener, daemon=True)
    listener_thread.start()

    print("FastAPI server started")
    print("Event listener started in background")

    yield

    # Shutdown
    print("Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Flare Credit Scoring API",
    description="Decentralized credit scoring and lending system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router, prefix="/api", tags=["credit"])

@app.get("/")
async def root():
    return {
        "message": "Flare Credit Scoring API",
        "docs": "/docs",
        "health": "/api/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
