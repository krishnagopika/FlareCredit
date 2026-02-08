import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.utils.config import Config


class OnChainAgent:
    """Analyzes on-chain blockchain behavior and scores with Gemini"""

    def __init__(self, blockchain_service):
        self.blockchain = blockchain_service
        self.llm = None
        if Config.GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=Config.GEMINI_API_KEY,
                temperature=0.1,
            )

    def analyze(self, state):
        """Analyze wallet's on-chain reputation"""
        user_address = state['user_address']

        print("OnChain Agent: Analyzing wallet...")

        # Get on-chain data
        data = self.blockchain.get_onchain_data(user_address)

        state['balance_eth'] = data['balance_eth']
        state['transaction_count'] = data['transaction_count']

        # Fetch FTSO prices for USD valuation
        ftso_prices = self.blockchain.get_ftso_prices()
        if ftso_prices:
            state['flr_price_usd'] = ftso_prices['flr_usd']
            state['xrp_price_usd'] = ftso_prices['xrp_usd']
            state['balance_usd'] = data['balance_eth'] * ftso_prices['flr_usd']
            print(f"  [OnChain] FTSO prices: FLR/USD=${ftso_prices['flr_usd']:.4f}, XRP/USD=${ftso_prices['xrp_usd']:.4f}")
            print(f"  [OnChain] FLR balance: {data['balance_eth']:.4f} FLR (${state['balance_usd']:.2f} USD via FTSO)")
        else:
            print("  [OnChain] FTSO price fetch failed, skipping USD valuation")

        # Enhanced analysis
        state['wallet_age_days'] = self._estimate_wallet_age(user_address, data['transaction_count'])
        state['is_active_user'] = data['transaction_count'] > 0

        # Calculate on-chain score via Gemini or fallback
        state['onchain_score'] = self._score_with_llm(state)

        print(f"  Balance: {state['balance_eth']:.4f} FLR")
        print(f"  Transactions: {state['transaction_count']}")
        print(f"  Est. Wallet Age: {state['wallet_age_days']} days")
        print(f"  OnChain Score: {state['onchain_score']}/100")

        return state

    def _estimate_wallet_age(self, address, tx_count):
        """Estimate wallet age based on transaction count"""
        if tx_count == 0:
            return 0
        estimated_days = min(tx_count * 7, 730)  # Cap at 2 years
        return estimated_days

    def _score_with_llm(self, state):
        """Use Gemini to score on-chain data, with rule-based fallback"""
        if not self.llm:
            print("  [OnChain] No Gemini API key, using rule-based scoring")
            return self._calculate_score(state)

        try:
            wallet_data = {
                "balance_flr": round(state['balance_eth'], 4),
                "balance_usd": round(state['balance_usd'], 2) if 'balance_usd' in state else None,
                "transaction_count": state['transaction_count'],
                "wallet_age_days": state['wallet_age_days'],
                "is_active_user": state['is_active_user'],
            }

            messages = [
                SystemMessage(content=(
                    "You are a blockchain reputation analyst. Analyze this wallet data and return "
                    "a JSON object with exactly two fields:\n"
                    '- "onchain_score": an integer from 0 to 100 (higher = better reputation)\n'
                    '- "reasoning": a brief explanation of your score\n\n'
                    "Consider wallet balance (in FLR and USD if available), transaction count (activity level), "
                    "wallet age, and whether the user is active. If balance_usd is provided, use it to "
                    "gauge real economic value. A wallet with high balance, many transactions, "
                    "and long history should score near 100. An empty or new wallet should score low.\n\n"
                    "Return ONLY valid JSON, no markdown formatting."
                )),
                HumanMessage(content=f"Wallet Data: {json.dumps(wallet_data)}"),
            ]

            response = self.llm.invoke(messages)
            result = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
            score = int(result['onchain_score'])
            score = max(0, min(100, score))

            print(f"  [OnChain] Gemini reasoning: {result.get('reasoning', 'N/A')}")
            return score

        except Exception as e:
            print(f"  [OnChain] Gemini call failed ({e}), falling back to rule-based scoring")
            return self._calculate_score(state)

    def _calculate_score(self, state):
        """Fallback: Calculate 0-100 reputation score with enhanced factors"""
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

        # Balance (30 points max) — use USD value if available for accuracy
        balance_usd = state.get('balance_usd')
        if balance_usd is not None:
            if balance_usd > 500:
                score += 30
            elif balance_usd > 200:
                score += 25
            elif balance_usd > 50:
                score += 20
            elif balance_usd > 20:
                score += 15
            elif balance_usd > 5:
                score += 10
            elif balance_usd > 0.5:
                score += 5
        else:
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
