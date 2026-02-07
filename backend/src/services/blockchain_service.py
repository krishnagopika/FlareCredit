from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import json
import time
from src.utils.config import Config

class BlockchainService:
    def __init__(self):
        # Connect to Flare
        self.w3 = Web3(Web3.HTTPProvider(Config.RPC_URL))
        
        # Inject POA middleware for Flare (updated for web3.py v7+)
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Setup agent account
        self.account = self.w3.eth.account.from_key(Config.PRIVATE_KEY)
        
        # Load contracts
        self.oracle = self._load_contract(Config.ORACLE_ABI_PATH, Config.ORACLE_ADDRESS)
        self.lending = self._load_contract(Config.LENDING_ABI_PATH, Config.LENDING_ADDRESS)
        self.token = self._load_contract(Config.TOKEN_ABI_PATH, Config.TOKEN_ADDRESS)
        
        # Verify connection
        if not self.w3.is_connected():
            raise Exception("Failed to connect to blockchain")
        
        print(f"Agent account: {self.account.address}")
        print(f"Connected to Flare Coston2")
        print(f"Oracle: {Config.ORACLE_ADDRESS}")
    
    def _load_contract(self, abi_path, address):
        """Load contract from ABI file"""
        with open(abi_path) as f:
            contract_json = json.load(f)
            abi = contract_json['abi']
        
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi
        )
    
    def listen_for_score_requests(self, callback):
        """Listen for CreditScoreRequested events"""
        print("\nListening for credit score requests...")
        print("Press Ctrl+C to stop\n")
        
        # Changed fromBlock to from_block (snake_case for web3.py v7+)
        event_filter = self.oracle.events.CreditScoreRequested.create_filter(
            from_block='latest'
        )
        
        while True:
            try:
                for event in event_filter.get_new_entries():
                    user_address = event['args']['user']
                    block_number = event['blockNumber']
                    tx_hash = event['transactionHash'].hex()
                    
                    print(f"\n{'='*60}")
                    print(f"NEW REQUEST")
                    print(f"User: {user_address}")
                    print(f"Block: {block_number}")
                    print(f"Tx: {tx_hash}")
                    print(f"{'='*60}\n")
                    
                    callback(user_address)
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("\nShutting down listener...")
                break
            except Exception as e:
                print(f"Error in listener: {e}")
                time.sleep(5)
    
    def submit_credit_score(self, user_address, score_data):
        """Submit credit score to oracle contract"""
        print(f"Submitting score to blockchain...")
        
        try:
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
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            
            print(f"Transaction sent: {tx_hash.hex()}")
            print(f"Waiting for confirmation...")
            
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt['status'] == 1:
                print(f"Score submitted successfully!")
                print(f"Gas used: {receipt['gasUsed']}")
            else:
                print(f"Transaction failed!")
            
            return receipt
            
        except Exception as e:
            print(f"Error submitting score: {e}")
            raise
    
    def get_onchain_data(self, user_address):
        """Get on-chain data for a user"""
        address = Web3.to_checksum_address(user_address)
        
        balance = self.w3.eth.get_balance(address)
        tx_count = self.w3.eth.get_transaction_count(address)
        
        return {
            'balance_wei': balance,
            'balance_eth': float(Web3.from_wei(balance, 'ether')),
            'transaction_count': tx_count
        }
    
    def get_user_score(self, user_address):
        """Get existing credit score for a user"""
        try:
            score = self.oracle.functions.getScore(
                Web3.to_checksum_address(user_address)
            ).call()
            
            return {
                'tradfi_score': score[0],
                'onchain_score': score[1],
                'combined_risk_score': score[2],
                'max_borrow_amount': score[3],
                'apr': score[4]
            }
        except Exception as e:
            print(f"Error getting score: {e}")
            return None
        

    def check_active_loan(self, user_address):
        """Check if user has an active loan"""
        try:
            loan = self.lending.functions.loans(
                Web3.to_checksum_address(user_address)
            ).call()
            
            # loan is a tuple: (amount, apr, timestamp, active)
            return loan[3]  # active boolean
            
        except Exception as e:
            print(f"Error checking loan status: {e}")
            return False

    def get_loan_info(self, user_address):
        """Get detailed loan information"""
        try:
            loan = self.lending.functions.loans(
                Web3.to_checksum_address(user_address)
            ).call()
            
            return {
                'amount': loan[0],
                'apr': loan[1],
                'timestamp': loan[2],
                'active': loan[3]
            }
            
        except Exception as e:
            print(f"Error getting loan info: {e}")
            return None

    def get_pool_balance(self):
        """Get lending pool balance"""
        try:
            balance = self.lending.functions.poolBalance().call()
            return {
                'balance_wei': balance,
                'balance_tokens': balance / 10**18
            }
        except Exception as e:
            print(f"Error getting pool balance: {e}")
            return None
        
    def disburse_loan(self, user_address, amount_wei):
        """
        Disburse loan in mUSDC to a user.
        amount_wei: int, amount in wei (e.g., 500000000000000000000 for 500 tokens)
        """
        amount = amount_wei  # Already in wei, don't convert
        amount_tokens = amount_wei / 10**18  # For display only

        print(f"Disbursing loan: {amount_tokens} mUSDC to {user_address}")

        try:
            # Debug: Check balances and allowances
            pool_balance = self.token.functions.balanceOf(self.account.address).call()
            print(f"Agent token balance: {pool_balance / 10**18} mUSDC")
            
            user_balance = self.token.functions.balanceOf(user_address).call()
            print(f"User token balance: {user_balance / 10**18} mUSDC")
            
            lending_balance = self.token.functions.balanceOf(self.lending.address).call()
            print(f"Lending contract balance: {lending_balance / 10**18} mUSDC")
            
            # Check if amount exceeds available balance
            if amount > pool_balance:
                error_msg = f"Insufficient pool balance. Available: {pool_balance / 10**18}, Requested: {amount_tokens}"
                print(error_msg)
                raise Exception(error_msg)

            # Approve lending contract if needed
            allowance = self.token.functions.allowance(
                self.account.address, 
                self.lending.address
            ).call()
            
            print(f"Current allowance: {allowance / 10**18} mUSDC")
            
            if allowance < amount:
                print("Approving lending contract to spend mUSDC...")
                approve_txn = self.token.functions.approve(
                    self.lending.address,
                    amount
                ).build_transaction({
                    'from': self.account.address,
                    'nonce': self.w3.eth.get_transaction_count(self.account.address),
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price
                })
                signed_approve = self.w3.eth.account.sign_transaction(
                    approve_txn, 
                    self.account.key
                )
                tx_hash = self.w3.eth.send_raw_transaction(signed_approve.raw_transaction)
                receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt['status'] != 1:
                    raise Exception("Token approval failed")
                    
                print(f"Approved {amount_tokens} mUSDC for lending contract.")

            # Try to call the function first to get revert reason
            try:
                self.lending.functions.disburseLoan(
                    Web3.to_checksum_address(user_address),
                    amount
                ).call({'from': self.account.address})
                print("Pre-flight check passed ✓")
            except Exception as call_error:
                print(f"Pre-flight check failed: {call_error}")
                raise Exception(f"Contract will revert: {str(call_error)}")

            # Call lending contract
            txn = self.lending.functions.disburseLoan(
                Web3.to_checksum_address(user_address),
                amount
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price
            })

            signed = self.w3.eth.account.sign_transaction(txn, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            print(f"Transaction sent: {tx_hash.hex()}")
            print("Waiting for confirmation...")

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] == 1:
                print(f"Loan disbursed successfully! Gas used: {receipt['gasUsed']}")
            else:
                # Try to get revert reason
                print(f"Transaction failed!")
                print(f"Receipt: {receipt}")
                
                # Attempt to replay transaction to get revert reason
                try:
                    self.w3.eth.call({
                        'to': self.lending.address,
                        'from': self.account.address,
                        'data': txn['data']
                    }, receipt['blockNumber'])
                except Exception as e:
                    print(f"Revert reason: {e}")
                
                raise Exception("Transaction reverted on-chain")

            return receipt

        except Exception as e:
            print(f"Error disbursing loan: {e}")
            raise

    def get_repayment_amount(self, user_address):
        """Get the total repayment amount including interest"""
        try:
            # Get loan info
            loan = self.get_loan_info(user_address)
            
            if not loan or not loan['active']:
                print("No active loan found")
                return None
            
            principal = loan['amount']
            apr = loan['apr']  # APR in basis points (e.g., 500 = 5%)
            timestamp = loan['timestamp']
            
            # Calculate time elapsed
            current_time = self.w3.eth.get_block('latest')['timestamp']
            time_elapsed = current_time - timestamp
            
            # Calculate interest: principal * (apr/10000) * (time_elapsed / 365 days)
            # Simple interest calculation
            seconds_per_year = 365 * 24 * 60 * 60
            interest = (principal * apr * time_elapsed) // (10000 * seconds_per_year)
            
            total_repayment = principal + interest
            
            print(f"Principal: {principal / 10**18} mUSDC")
            print(f"APR: {apr / 100}%")
            print(f"Time elapsed: {time_elapsed} seconds ({time_elapsed / 86400:.2f} days)")
            print(f"Interest: {interest / 10**18} mUSDC")
            print(f"Total repayment: {total_repayment / 10**18} mUSDC")
            
            return {
                'repayment_amount_wei': total_repayment,
                'repayment_amount_tokens': total_repayment / 10**18,
                'principal_wei': principal,
                'principal_tokens': principal / 10**18,
                'interest_wei': interest,
                'interest_tokens': interest / 10**18,
                'time_elapsed_seconds': time_elapsed,
                'time_elapsed_days': time_elapsed / 86400
            }
        except Exception as e:
            print(f"Error getting repayment amount: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_user_token_balance(self, user_address):
        """Get user's mUSDC token balance"""
        try:
            balance = self.token.functions.balanceOf(
                Web3.to_checksum_address(user_address)
            ).call()
            
            return {
                'balance_wei': balance,
                'balance_tokens': balance / 10**18
            }
        except Exception as e:
            print(f"Error getting token balance: {e}")
            return None

    def get_token_allowance(self, owner_address, spender_address):
        """Get token allowance"""
        try:
            allowance = self.token.functions.allowance(
                Web3.to_checksum_address(owner_address),
                Web3.to_checksum_address(spender_address)
            ).call()
            
            return {
                'allowance_wei': allowance,
                'allowance_tokens': allowance / 10**18
            }
        except Exception as e:
            print(f"Error getting allowance: {e}")
            return None