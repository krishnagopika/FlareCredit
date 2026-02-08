from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import os

# REPLACE THIS WITH THE ACTUAL PRIVATE KEY
USER_PRIVATE_KEY = os.getenv("USER_PRIVATE_KEY")  # Get from MetaMask

# Connect to Flare Coston2
w3 = Web3(Web3.HTTPProvider("https://coston2-api.flare.network/ext/C/rpc"))
w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

# User account
user = w3.eth.account.from_key(USER_PRIVATE_KEY)
print(f"Repaying from: {user.address}")

# Get the latest nonce for the user
nonce = w3.eth.get_transaction_count(user.address)

# Transaction 1: Approve
print("\n=== STEP 1: Approving tokens ===")
tx1 = {
    'to': Web3.to_checksum_address("0x45c7B48d002D014D0F8C8dff55045016AD28ACCB"),
    'data': "0x095ea7b30000000000000000000000002860e5acd371978b8aa3c6a6a4ac0986b27443f800000000000000000000000000000000000000000000001b1ae8f85ab3ae935a",
    'value': 0,
    'gas': int("0x186a0", 16),
    'gasPrice': int("0x5d21dba01", 16),
    'nonce': nonce,
    'chainId': 114
}

signed_tx1 = w3.eth.account.sign_transaction(tx1, USER_PRIVATE_KEY)
tx_hash1 = w3.eth.send_raw_transaction(signed_tx1.raw_transaction)
print(f"Approve tx sent: {tx_hash1.hex()}")

receipt1 = w3.eth.wait_for_transaction_receipt(tx_hash1)
print(f"Approve tx confirmed: {receipt1['status'] == 1}")

# Transaction 2: Repay
print("\n=== STEP 2: Repaying loan ===")
tx2 = {
    'to': Web3.to_checksum_address("0x9feF5655Ad38c61E6F662c5aED8174dcde2fd788"),
    'data': "0x402d8883",
    'value': 0,
    'gas': int("0x493e0", 16),
    'gasPrice': int("0x5d21dba01", 16),
    'nonce': nonce + 1,  # Increment nonce
    'chainId': 114
}

signed_tx2 = w3.eth.account.sign_transaction(tx2, USER_PRIVATE_KEY)
tx_hash2 = w3.eth.send_raw_transaction(signed_tx2.raw_transaction)
print(f"Repay tx sent: {tx_hash2.hex()}")

receipt2 = w3.eth.wait_for_transaction_receipt(tx_hash2)
print(f"Repay tx confirmed: {receipt2['status'] == 1}")

print("\n✅ LOAN REPAID SUCCESSFULLY!")
