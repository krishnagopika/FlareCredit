from web3 import Web3
import time

class OnChainAgent:
    """Analyzes on-chain blockchain behavior"""
    
    def __init__(self, blockchain_service):
        self.blockchain = blockchain_service
    
    def analyze(self, state):
        """Analyze wallet's on-chain reputation"""
        user_address = state['user_address']
        
        print("OnChain Agent: Analyzing wallet...")
        
        # Get on-chain data
        data = self.blockchain.get_onchain_data(user_address)
        
        state['balance_eth'] = data['balance_eth']
        state['transaction_count'] = data['transaction_count']
        
        # Enhanced analysis
        state['wallet_age_days'] = self._estimate_wallet_age(user_address, data['transaction_count'])
        state['is_active_user'] = data['transaction_count'] > 0
        
        # Calculate on-chain score
        state['onchain_score'] = self._calculate_score(state)
        
        print(f"  Balance: {state['balance_eth']:.4f} FLR")
        print(f"  Transactions: {state['transaction_count']}")
        print(f"  Est. Wallet Age: {state['wallet_age_days']} days")
        print(f"  OnChain Score: {state['onchain_score']}/100")
        
        return state
    
    def _estimate_wallet_age(self, address, tx_count):
        """Estimate wallet age based on transaction count"""
        # Rough estimate: average user makes 1 tx per week
        # More sophisticated version would query block explorer
        
        if tx_count == 0:
            return 0
        
        # Estimate: 1 transaction per 7 days on average
        estimated_days = min(tx_count * 7, 730)  # Cap at 2 years
        
        return estimated_days
    
    def _calculate_score(self, state):
        """Calculate 0-100 reputation score with enhanced factors"""
        score = 0
        
        # Transaction count (30 points max)
        tx_count = state['transaction_count']
        if tx_count > 100:
            score += 30
        elif tx_count > 50:
            score += 25
        elif tx_count > 20:
            score += 20
        elif tx_count > 10:
            score += 15
        elif tx_count > 5:
            score += 10
        
        # Balance (30 points max)
        balance = state['balance_eth']
        if balance > 100:
            score += 30
        elif balance > 50:
            score += 25
        elif balance > 10:
            score += 20
        elif balance > 5:
            score += 15
        elif balance > 1:
            score += 10
        elif balance > 0.1:
            score += 5
        
        # Wallet age (25 points max)
        age_days = state.get('wallet_age_days', 0)
        if age_days > 365:
            score += 25
        elif age_days > 180:
            score += 20
        elif age_days > 90:
            score += 15
        elif age_days > 30:
            score += 10
        elif age_days > 7:
            score += 5
        
        # Active user bonus (15 points)
        if state.get('is_active_user', False):
            score += 15
        
        return min(100, score)