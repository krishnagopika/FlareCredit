import json
import time
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from src.utils.config import Config


class RiskAgent:
    """Combines TradFi + OnChain into risk assessment using Claude"""

    def __init__(self, blockchain_service=None):
        self.blockchain_service = blockchain_service
        self.llm = ChatBedrockConverse(
            model=Config.BEDROCK_MODEL_ID,
            region_name=Config.AWS_REGION,
            temperature=0.1,
        )

    def calculate_risk(self, state):
        """Calculate final risk metrics via Claude or fallback"""

        print("Risk Agent: Calculating risk scores...")

        requested_amount = state.get('requested_amount', 0)

        # Try LLM-based risk assessment
        llm_result = self._assess_with_llm(state)

        if llm_result:
            state['combined_risk_score'] = llm_result['combined_risk_score']
            state['max_borrow_amount'] = llm_result['max_borrow_amount']
            state['apr'] = llm_result['apr']
        else:
            # Fallback to rule-based
            self._calculate_rule_based(state)

        # Apply Flare RNG jitter to APR (±50 basis points)
        self._apply_rng_jitter(state)

        # Approved amount logic
        if requested_amount > 0:
            state['approved_amount'] = min(requested_amount, state['max_borrow_amount'])
        else:
            state['approved_amount'] = state['max_borrow_amount']

        # Valid for 30 days
        state['valid_until'] = int(time.time()) + (30 * 24 * 60 * 60)

        # Compute USD loan values using FTSO XRP/USD price
        xrp_price = state.get('xrp_price_usd')
        if xrp_price:
            state['loan_value_usd'] = (state['approved_amount'] / 10**18) * xrp_price
            state['max_borrow_usd'] = (state['max_borrow_amount'] / 10**18) * xrp_price

        print(f"  Risk Score: {state['combined_risk_score']}/100")
        print(f"  Max Borrow: {state['max_borrow_amount'] / 10**18:.0f} tokens")

        if requested_amount > 0:
            print(f"  Requested: {requested_amount / 10**18:.0f} tokens")
            print(f"  Approved: {state['approved_amount'] / 10**18:.0f} tokens")
            utilization = requested_amount / state['max_borrow_amount'] if state['max_borrow_amount'] > 0 else 0
            print(f"  Utilization: {utilization * 100:.1f}%")

        print(f"  APR: {state['apr'] / 100}%")

        if xrp_price:
            print(f"  [Risk] Loan value: ${state['loan_value_usd']:.2f} USD (XRP @ ${xrp_price:.4f} via FTSO)")

        return state

    def _apply_rng_jitter(self, state):
        """Apply ±50 bps jitter to APR using Flare Secure RNG"""
        if not self.blockchain_service:
            return

        try:
            rng = self.blockchain_service.get_secure_random()
            random_number = rng['random_number']
            jitter = (random_number % 101) - 50  # range: -50 to +50 bps
            base_apr = state['apr']
            state['apr'] = max(300, min(600, base_apr + jitter))
            state['rng_jitter'] = jitter
            sign = '+' if jitter >= 0 else ''
            print(f"  [Risk] Flare RNG jitter: {sign}{jitter} bps (secure={rng['is_secure']})")
        except Exception as e:
            print(f"  [Risk] Flare RNG call failed ({e}), skipping jitter")

    def _assess_with_llm(self, state):
        """Use Claude for risk assessment, returns dict or None on failure"""
        try:
            requested_amount = state.get('requested_amount', 0)
            input_data = {
                "tradfi_score": state['tradfi_score'],
                "tradfi_score_range": "0-1000 (higher = more creditworthy)",
                "onchain_score": state['onchain_score'],
                "onchain_score_range": "0-100 (higher = better reputation)",
                "requested_amount_tokens": requested_amount / 10**18 if requested_amount > 0 else "not specified",
            }

            messages = [
                SystemMessage(content=(
                    "You are a DeFi risk assessor. Given a borrower's TradFi credit score and "
                    "on-chain reputation score, determine their risk level and loan terms.\n\n"
                    "Return a JSON object with exactly these fields:\n"
                    '- "combined_risk_score": integer 0-100 (lower = less risky, better borrower)\n'
                    '- "max_borrow_amount_tokens": integer, max tokens the user can borrow '
                    "(range: 1000-50000 based on risk)\n"
                    '- "apr_basis_points": integer, annual percentage rate in basis points '
                    "(e.g. 500 = 5%). Range 300-600 based on risk. Low risk ~300, high risk ~600.\n"
                    '- "reasoning": brief explanation\n\n'
                    "Risk mapping guide:\n"
                    "- Excellent (risk 0-20): tradfi > 800, onchain > 70 → max 50000 tokens, APR ~300-350\n"
                    "- Good (risk 21-40): tradfi 600-800, onchain 50-70 → max 25000 tokens, APR ~350-420\n"
                    "- Fair (risk 41-60): tradfi 400-600, onchain 30-50 → max 10000 tokens, APR ~420-500\n"
                    "- Poor (risk 61-80): tradfi 200-400, onchain 15-30 → max 5000 tokens, APR ~500-550\n"
                    "- High risk (81-100): tradfi < 200, onchain < 15 → max 1000 tokens, APR ~550-600\n\n"
                    "If a requested amount is specified, factor the utilization ratio into APR "
                    "(higher utilization = slightly higher APR, up to +200 basis points).\n\n"
                    "Return ONLY valid JSON, no markdown formatting."
                )),
                HumanMessage(content=f"Borrower Data: {json.dumps(input_data)}"),
            ]

            response = self.llm.invoke(messages)
            result = json.loads(response.content.strip().removeprefix("```json").removesuffix("```").strip())

            combined_risk = max(0, min(100, int(result['combined_risk_score'])))
            max_borrow_tokens = max(1000, min(50000, int(result['max_borrow_amount_tokens'])))
            apr = max(300, min(600, int(result['apr_basis_points'])))

            print(f"  [Risk] Claude reasoning: {result.get('reasoning', 'N/A')}")

            return {
                'combined_risk_score': combined_risk,
                'max_borrow_amount': max_borrow_tokens * 10**18,
                'apr': apr,
            }

        except Exception as e:
            print(f"  [Risk] LLM call failed ({e}), falling back to rule-based scoring")
            return None

    def _calculate_rule_based(self, state):
        """Fallback rule-based risk calculation"""
        # Combined risk score (0-100, lower = better)
        tradfi_risk = (1000 - state['tradfi_score']) / 10
        onchain_risk = (100 - state['onchain_score'])

        # Weight: 60% TradFi, 40% OnChain
        combined = (tradfi_risk * 0.6) + (onchain_risk * 0.4)
        state['combined_risk_score'] = int(combined)

        # Max borrow
        state['max_borrow_amount'] = self._max_borrow(state)

        # APR
        requested_amount = state.get('requested_amount', 0)
        if requested_amount > 0:
            state['apr'] = self._calculate_apr_with_amount(state, requested_amount)
        else:
            state['apr'] = self._calculate_apr(state)

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
        base_apr = self._calculate_apr(state)

        max_amount = state['max_borrow_amount']
        if max_amount == 0:
            return base_apr

        utilization = min(requested_amount / max_amount, 1.0)
        utilization_premium = int(utilization * 200)

        amount_in_tokens = requested_amount / 10**18
        if amount_in_tokens > 20000:
            amount_premium = 50
        elif amount_in_tokens > 10000:
            amount_premium = 25
        else:
            amount_premium = 0

        adjusted_apr = base_apr + utilization_premium + amount_premium

        print(f"  Base APR: {base_apr / 100}%")
        print(f"  Utilization Premium: {utilization_premium / 100}%")
        print(f"  Amount Premium: {amount_premium / 100}%")

        return adjusted_apr
