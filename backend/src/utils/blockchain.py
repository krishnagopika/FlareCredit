# utils/blockchain.py
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import os
from dotenv import load_dotenv
import time

load_dotenv()

class BlockchainClient:
    def __init__(self):
        # Connect to Flare Coston2
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        
        # Your agent account
        self.account = self.w3.eth.account.from_key(os.getenv('PRIVATE_KEY'))
        print(f" Agent account: {self.account.address}")
        
        # Load Oracle contract (THE MAIN ONE YOU NEED)
        self.oracle = self._load_contract('oracle_abi.json', 'ORACLE_ADDRESS')
        
        # Optional: Load lending & token contracts
        self.lending = self._load_contract('lending_abi.json', 'LENDING_ADDRESS')
        self.token = self._load_contract('token_abi.json', 'TOKEN_ADDRESS')
        
        # Verify connection
        if self.w3.is_connected():
            print(f" Connected to Flare Coston2")
            print(f"Oracle:  {os.getenv('ORACLE_ADDRESS')}")
        else:
            raise Exception("Failed to connect to blockchain")
    
    def _load_contract(self, abi_filename: str, address_env_var: str):
        """Load contract from ABI file"""
        with open(f'contracts/{abi_filename}') as f:
            contract_json = json.load(f)
            abi = contract_json['abi']  # Extract just the ABI array
        
        address = Web3.to_checksum_address(os.getenv(address_env_var))
        return self.w3.eth.contract(address=address, abi=abi)
    
    def listen_for_score_requests(self, callback):
        """Listen for CreditScoreRequested events"""
        print("\n🎧 Listening for credit score requests...")
        
        event_filter = self.oracle.events.CreditScoreRequested.create_filter(
            fromBlock='latest'
        )
        
        while True:
            try:
                for event in event_filter.get_new_entries():
                    user_address = event['args']['user']
                    print(f"\n NEW REQUEST from: {user_address}")
                    callback(user_address)
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\n Shutting down...")
                break
            except Exception as e:
                print(f" Error: {e}")
                time.sleep(5)
    
    def submit_credit_score(self, user_address: str, score_data: dict):
        """Submit credit score to oracle"""
        print(f" Submitting score...")
        
        txn = self.oracle.functions.submitCreditScore(
            Web3.to_checksum_address(user_address),
            score_data['tradfi_score'],
            score_data['onchain_score'],
            score_data['combined_risk_score'],
            score_data['max_borrow_amount'],
            score_data['apr'],
            score_data['valid_until']
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        signed = self.w3.eth.account.sign_transaction(txn, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        
        print(f" Waiting for confirmation...")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt['status'] == 1:
            print(f" Score submitted! Gas used: {receipt['gasUsed']}")
        else:
            print(f"Transaction failed!")
        
        return receipt
    
    def get_user_onchain_data(self, user_address: str):
        """Get on-chain metrics for a user"""
        address = Web3.to_checksum_address(user_address)
        balance = self.w3.eth.get_balance(address)
        tx_count = self.w3.eth.get_transaction_count(address)
        
        return {
            'balance_wei': balance,
            'balance_eth': float(Web3.from_wei(balance, 'ether')),
            'transaction_count': tx_count
        }