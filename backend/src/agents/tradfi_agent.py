import json
import os
from src.utils.config import Config

class TradFiAgent:
    """Fetches traditional finance credit data"""
    
    def __init__(self):
        self.data_file = Config.MOCK_DATA_PATH
        self._load_data()
    
    def _load_data(self):
        """Load mock credit data from JSON"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                self.credit_database = json.load(f)
        else:
            self.credit_database = {}
            print(f"Warning: {self.data_file} not found, will generate data")
    
    def fetch_data(self, state):
        """Fetch credit data for a user"""
        user_address = state['user_address']
        
        print("TradFi Agent: Fetching credit data...")
        
        # Try exact match first
        if user_address in self.credit_database:
            data = self.credit_database[user_address]
            print(f"  Found exact match for {user_address}")
        else:
            # Generate deterministic data
            print(f"  Generating data for {user_address}")
            data = self._generate_data(user_address)
        
        # Store in state
        state['experian_data'] = data['experian']
        state['plaid_data'] = data['plaid']
        state['payment_data'] = data['payment_history']
        
        # Calculate TradFi score
        state['tradfi_score'] = self._calculate_score(state)
        
        print(f"  FICO: {state['experian_data']['fico_score']}")
        print(f"  TradFi Score: {state['tradfi_score']}/1000")
        
        return state
    
    def _generate_data(self, address):
        """Generate deterministic mock data from address"""
        seed = int(address[-8:], 16) % 1000
        
        fico_base = 550 + (seed % 270)
        
        return {
            "experian": {
                "fico_score": fico_base,
                "account_age_months": 12 + (seed % 168),
                "payment_history_percent": 70.0 + (seed % 30),
                "credit_utilization_percent": 5.0 + (seed % 80),
                "total_accounts": 2 + (seed % 23),
                "derogatory_marks": seed % 4,
                "total_debt": (seed % 50) * 1000
            },
            "plaid": {
                "checking_balance": (seed % 250) * 100,
                "savings_balance": (seed % 500) * 100,
                "avg_monthly_income": 2000 + (seed % 130) * 100,
                "avg_monthly_expenses": 1500 + (seed % 105) * 100,
                "overdraft_count_6mo": seed % 6
            },
            "payment_history": {
                "on_time_payments_12mo": 6 + (seed % 7),
                "late_payments_12mo": seed % 5,
                "missed_payments_12mo": seed % 3,
                "debt_to_income_ratio": 0.1 + (seed % 10) * 0.1
            }
        }
    
    def _calculate_score(self, state):
        """Convert multiple metrics into 0-1000 score"""
        exp = state['experian_data']
        plaid = state['plaid_data']
        payment = state['payment_data']
        
        # Base from FICO (40% weight)
        fico_component = (exp['fico_score'] - 300) / 550 * 400
        
        # Payment history (30% weight)
        total_payments = (payment['on_time_payments_12mo'] + 
                         payment['late_payments_12mo'] + 
                         payment['missed_payments_12mo'])
        
        if total_payments > 0:
            payment_pct = payment['on_time_payments_12mo'] / total_payments
        else:
            payment_pct = 0
        
        payment_component = payment_pct * 300
        
        # Banking health (20% weight)
        total_savings = plaid['checking_balance'] + plaid['savings_balance']
        savings_component = min(total_savings / 25000, 1) * 200
        
        # Credit utilization penalty (10% weight)
        utilization_penalty = exp['credit_utilization_percent'] * -1
        
        score = (fico_component + payment_component + 
                savings_component + utilization_penalty)
        
        return int(max(0, min(1000, score)))