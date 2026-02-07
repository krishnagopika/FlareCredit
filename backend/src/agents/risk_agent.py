import time

class RiskAgent:
    """Combines TradFi + OnChain into risk assessment"""
    
    def calculate_risk(self, state):
        """Calculate final risk metrics"""
        
        print("Risk Agent: Calculating risk scores...")
        
        # Combined risk score (0-100, lower = better)
        tradfi_risk = (1000 - state['tradfi_score']) / 10
        onchain_risk = (100 - state['onchain_score'])
        
        # Weight: 60% TradFi, 40% OnChain
        combined = (tradfi_risk * 0.6) + (onchain_risk * 0.4)
        state['combined_risk_score'] = int(combined)
        
        # Calculate loan parameters
        state['max_borrow_amount'] = self._max_borrow(state)
        
        # Calculate APR based on risk and requested amount
        requested_amount = state.get('requested_amount', 0)
        if requested_amount > 0:
            state['apr'] = self._calculate_apr_with_amount(state, requested_amount)
            state['approved_amount'] = min(requested_amount, state['max_borrow_amount'])
        else:
            state['apr'] = self._calculate_apr(state)
            state['approved_amount'] = state['max_borrow_amount']
        
        # Valid for 30 days
        state['valid_until'] = int(time.time()) + (30 * 24 * 60 * 60)
        
        print(f"  Risk Score: {state['combined_risk_score']}/100")
        print(f"  Max Borrow: {state['max_borrow_amount'] / 10**18:.0f} tokens")
        
        if requested_amount > 0:
            print(f"  Requested: {requested_amount / 10**18:.0f} tokens")
            print(f"  Approved: {state['approved_amount'] / 10**18:.0f} tokens")
            utilization = requested_amount / state['max_borrow_amount'] if state['max_borrow_amount'] > 0 else 0
            print(f"  Utilization: {utilization * 100:.1f}%")
        
        print(f"  APR: {state['apr'] / 100}%")
        
        return state
    
    def _max_borrow(self, state):
        """Max borrow in wei (18 decimals)"""
        risk = state['combined_risk_score']
        
        if risk <= 20:      # Excellent
            return 50000 * 10**18
        elif risk <= 40:    # Good
            return 25000 * 10**18
        elif risk <= 60:    # Fair
            return 10000 * 10**18
        elif risk <= 80:    # Poor
            return 5000 * 10**18
        else:               # High risk
            return 1000 * 10**18
    
    def _calculate_apr(self, state):
        """Base APR in basis points (500 = 5%)"""
        risk = state['combined_risk_score']
        
        # Base 3% + risk premium
        base = 300
        premium = int(risk * 3)  # 0-300 bps based on risk
        
        return base + premium
    
    def _calculate_apr_with_amount(self, state, requested_amount):
        """APR adjusted for loan amount and utilization"""
        
        # Get base APR from risk
        base_apr = self._calculate_apr(state)
        
        # Calculate utilization of credit limit
        max_amount = state['max_borrow_amount']
        if max_amount == 0:
            return base_apr
        
        utilization = min(requested_amount / max_amount, 1.0)
        
        # Add utilization premium (0-2% based on how much they're borrowing)
        # Higher utilization = higher rate
        utilization_premium = int(utilization * 200)  # 0-200 basis points
        
        # Add amount-based premium (larger absolute amounts = slightly higher rate)
        amount_in_tokens = requested_amount / 10**18
        if amount_in_tokens > 20000:
            amount_premium = 50  # +0.5%
        elif amount_in_tokens > 10000:
            amount_premium = 25  # +0.25%
        else:
            amount_premium = 0
        
        adjusted_apr = base_apr + utilization_premium + amount_premium
        
        print(f"  Base APR: {base_apr / 100}%")
        print(f"  Utilization Premium: {utilization_premium / 100}%")
        print(f"  Amount Premium: {amount_premium / 100}%")
        
        return adjusted_apr