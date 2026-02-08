import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from src.utils.config import Config


class TradFiAgent:
    """Fetches traditional finance credit data via Flare FDC and scores with Gemini"""

    def __init__(self, fdc_service):
        self.fdc = fdc_service
        self.llm = None
        if Config.GEMINI_API_KEY:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=Config.GEMINI_API_KEY,
                temperature=0.1,
            )

    def fetch_data(self, state):
        """Fetch credit data for a user through FDC-validated external source"""
        user_address = state['user_address']

        print("TradFi Agent: Fetching credit data via Flare FDC...")

        # Fetch from external source through FDC attestation
        data = self.fdc.fetch_credit_data(user_address)

        if data and 'experian' in data:
            print(f"  Retrieved externally validated data for {user_address}")
        else:
            # Fallback: generate deterministic data if external source unavailable
            print(f"  External source unavailable, generating data for {user_address}")
            data = self._generate_data(user_address)

        # Store in state
        state['experian_data'] = data['experian']
        state['plaid_data'] = data['plaid']
        state['payment_data'] = data['payment_history']

        # Calculate TradFi score via Gemini or fallback
        state['tradfi_score'] = self._score_with_llm(state)

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

    def _score_with_llm(self, state):
        """Use Gemini to score credit data, with rule-based fallback"""
        if not self.llm:
            print("  [TradFi] No Gemini API key, using rule-based scoring")
            return self._calculate_score(state)

        try:
            exp = state['experian_data']
            plaid = state['plaid_data']
            payment = state['payment_data']

            messages = [
                SystemMessage(content=(
                    "You are a credit analyst AI. Analyze the provided credit data and return "
                    "a JSON object with exactly two fields:\n"
                    '- "tradfi_score": an integer from 0 to 1000 (higher = more creditworthy)\n'
                    '- "reasoning": a brief explanation of your score\n\n'
                    "Consider FICO score, payment history, credit utilization, banking health, "
                    "debt-to-income ratio, and account age. Weight FICO heavily (~40%), "
                    "payment history (~30%), banking health (~20%), and utilization (~10%).\n\n"
                    "Return ONLY valid JSON, no markdown formatting."
                )),
                HumanMessage(content=(
                    f"Experian Data: {json.dumps(exp)}\n\n"
                    f"Plaid Banking Data: {json.dumps(plaid)}\n\n"
                    f"Payment History: {json.dumps(payment)}"
                )),
            ]

            response = self.llm.invoke(messages)
            result = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())
            score = int(result['tradfi_score'])
            score = max(0, min(1000, score))

            print(f"  [TradFi] Gemini reasoning: {result.get('reasoning', 'N/A')}")
            return score

        except Exception as e:
            print(f"  [TradFi] Gemini call failed ({e}), falling back to rule-based scoring")
            return self._calculate_score(state)

    def _calculate_score(self, state):
        """Fallback: Convert multiple metrics into 0-1000 score"""
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
