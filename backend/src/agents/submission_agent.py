class SubmissionAgent:
    """Submits score to oracle contract"""
    
    def __init__(self, blockchain_service):
        self.blockchain = blockchain_service
    
    def submit(self, state):
        """Submit to blockchain"""
        
        print("Submission Agent: Sending to oracle...")
        
        score_data = {
            'tradfi_score': state['tradfi_score'],
            'onchain_score': state['onchain_score'],
            'combined_risk_score': state['combined_risk_score'],
            'max_borrow_amount': state['max_borrow_amount'],
            'apr': state['apr'],
            'valid_until': state['valid_until']
        }
        
        receipt = self.blockchain.submit_credit_score(
            state['user_address'],
            score_data
        )
        
        state['tx_hash'] = receipt['transactionHash'].hex()
        state['completed'] = True
        
        return state