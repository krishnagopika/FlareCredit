from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="FlareCredit Faucet", description="Mint mUSDC test tokens on Coston2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Flare Coston2
RPC_URL = os.getenv("RPC_URL", "https://coston2-api.flare.network/ext/C/rpc")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS", "0x45c7B48d002D014D0F8C8dff55045016AD28ACCB")

if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY is required in .env")

w3 = Web3(Web3.HTTPProvider(RPC_URL))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
account = w3.eth.account.from_key(PRIVATE_KEY)

# Minimal ERC-20 ABI with mint
TOKEN_ABI = [
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "mint",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

token = w3.eth.contract(address=Web3.to_checksum_address(TOKEN_ADDRESS), abi=TOKEN_ABI)

print(f"Faucet ready | Token: {TOKEN_ADDRESS} | Signer: {account.address}")


class MintRequest(BaseModel):
    address: str
    amount: float = 10000  # default 10k mUSDC


@app.post("/mint")
def mint_tokens(req: MintRequest):
    """Mint mUSDC to a wallet address."""
    try:
        to = Web3.to_checksum_address(req.address)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    if req.amount <= 0 or req.amount > 1_000_000:
        raise HTTPException(status_code=400, detail="Amount must be between 0 and 1,000,000")

    amount_wei = int(req.amount * 10**18)

    try:
        txn = token.functions.mint(to, amount_wei).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 100000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = w3.eth.account.sign_transaction(txn, account.key)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt["status"] != 1:
            raise HTTPException(status_code=500, detail="Mint transaction reverted")

        balance = token.functions.balanceOf(to).call()

        return {
            "success": True,
            "address": to,
            "minted": req.amount,
            "tx_hash": tx_hash.hex(),
            "new_balance": balance / 10**18,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mint failed: {str(e)}")


@app.get("/balance/{address}")
def get_balance(address: str):
    """Check mUSDC balance for an address."""
    try:
        addr = Web3.to_checksum_address(address)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid wallet address")

    balance = token.functions.balanceOf(addr).call()
    return {"address": addr, "balance": balance / 10**18}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
