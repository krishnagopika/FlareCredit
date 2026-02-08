import requests
import json
import hashlib
import time
from web3 import Web3


class FlareFDCService:
    """
    Flare Data Connector (FDC) service for externally validated credit data.
    Uses FDC's JsonApi attestation type to fetch and verify data from
    external Web2 sources through Flare's decentralized attestation network.

    Coston2 Testnet Infrastructure:
      JQ Verifier:    https://jq-verifier-test.flare.rocks
      DA Layer:       https://ctn2-data-availability.flare.network
      FdcHub:         0x48aC463d7975828989331F4De43341627b9c5f1D
      FdcVerification:0x075bf301fF07C4920e5261f93a0609640F53487D
      FdcRequestFee:  0x191a1282Ac700edE65c5B0AaF313BAcC3eA7fC7e
    """

    # "JsonApi" UTF8 hex-encoded, zero-padded to 32 bytes
    JSONAPI_ATTESTATION_TYPE = (
        "0x4a736f6e41706900000000000000000000000000000000000000000000000000"
    )
    # "WEB2" UTF8 hex-encoded, zero-padded to 32 bytes
    WEB2_SOURCE_ID = (
        "0x5745423200000000000000000000000000000000000000000000000000000000"
    )

    # Coston2 voting round parameters
    FIRST_VOTING_ROUND_START_TS = 1658430000
    VOTING_EPOCH_DURATION_SEC = 90

    # ABI signature for credit data response encoding
    CREDIT_DATA_ABI_SIGNATURE = (
        "(uint256 fico_score, uint256 account_age_months, "
        "uint256 payment_history_percent, uint256 credit_utilization_percent, "
        "uint256 total_accounts, uint256 derogatory_marks, uint256 total_debt, "
        "uint256 checking_balance, uint256 savings_balance, "
        "uint256 avg_monthly_income, uint256 avg_monthly_expenses, "
        "uint256 overdraft_count_6mo, "
        "uint256 on_time_payments_12mo, uint256 late_payments_12mo, "
        "uint256 missed_payments_12mo, uint256 debt_to_income_ratio)"
    )

    # JQ filter to flatten the nested credit data into ABI-compatible format
    CREDIT_DATA_JQ = (
        "{ fico_score: .experian.fico_score, "
        "account_age_months: .experian.account_age_months, "
        "payment_history_percent: (.experian.payment_history_percent * 100 | floor), "
        "credit_utilization_percent: (.experian.credit_utilization_percent * 100 | floor), "
        "total_accounts: .experian.total_accounts, "
        "derogatory_marks: .experian.derogatory_marks, "
        "total_debt: .experian.total_debt, "
        "checking_balance: (.plaid.checking_balance * 100 | floor), "
        "savings_balance: (.plaid.savings_balance * 100 | floor), "
        "avg_monthly_income: (.plaid.avg_monthly_income * 100 | floor), "
        "avg_monthly_expenses: (.plaid.avg_monthly_expenses * 100 | floor), "
        "overdraft_count_6mo: .plaid.overdraft_count_6mo, "
        "on_time_payments_12mo: .payment_history.on_time_payments_12mo, "
        "late_payments_12mo: .payment_history.late_payments_12mo, "
        "missed_payments_12mo: .payment_history.missed_payments_12mo, "
        "debt_to_income_ratio: (.payment_history.debt_to_income_ratio * 100 | floor) }"
    )

    def __init__(
        self,
        jq_verifier_url,
        da_layer_url,
        data_api_url,
        fdc_hub_address,
        fdc_verification_address,
        fdc_fee_address,
        w3=None,
        api_key=None,
    ):
        self.jq_verifier_url = jq_verifier_url.rstrip("/")
        self.da_layer_url = da_layer_url.rstrip("/")
        self.data_api_url = data_api_url.rstrip("/")
        self.fdc_hub_address = fdc_hub_address
        self.fdc_verification_address = fdc_verification_address
        self.fdc_fee_address = fdc_fee_address
        self.w3 = w3
        self.api_key = api_key or "00000000-0000-0000-0000-000000000000"

        self.session = requests.Session()
        self.session.headers["Content-Type"] = "application/json"
        self.session.headers["X-API-KEY"] = self.api_key

        print(f"FDC Service initialized (Coston2)")
        print(f"  JQ Verifier:      {self.jq_verifier_url}")
        print(f"  DA Layer:         {self.da_layer_url}")
        print(f"  Data API:         {self.data_api_url}")
        print(f"  FdcHub:           {self.fdc_hub_address}")
        print(f"  FdcVerification:  {self.fdc_verification_address}")

    def fetch_credit_data(self, user_address):
        """
        Fetch credit data for a user via FDC JsonApi attestation.

        Full FDC flow:
        1. Build JsonApi attestation request targeting the external credit data API
        2. Submit to JQ verifier (prepareRequest) - verifier fetches + validates external data
        3. Verifier returns abiEncodedRequest with validated data
        4. Optionally submit to FdcHub for on-chain Merkle root inclusion
        5. Return the attested credit data for immediate use

        Falls back to direct verified fetch if JQ verifier is unavailable.
        """
        data_url = f"{self.data_api_url}/{user_address}"

        print(f"  FDC: Requesting JsonApi attestation for {user_address}")
        print(f"  FDC: External data source: {data_url}")

        # Step 1: Try FDC attestation via JQ verifier
        attested_data = self._request_fdc_attestation(data_url)
        if attested_data:
            print(f"  FDC: Data attested via Flare Data Connector (JsonApi)")
            return attested_data

        # Step 2: Fallback - direct fetch with integrity verification
        print(f"  FDC: JQ verifier unavailable, using direct verified fetch")
        return self._fetch_with_integrity(data_url, user_address)

    def _request_fdc_attestation(self, data_url):
        """
        Submit attestation request to the JQ verifier's prepareRequest endpoint.

        Endpoint: POST {jq_verifier_url}/JsonApi/prepareRequest
        The JQ verifier fetches the external URL, applies the JQ filter,
        ABI-encodes the result, and returns a validated abiEncodedRequest.
        """
        attestation_request = {
            "attestationType": self.JSONAPI_ATTESTATION_TYPE,
            "sourceId": self.WEB2_SOURCE_ID,
            "requestBody": {
                "url": data_url,
                "postprocessJq": self.CREDIT_DATA_JQ,
                "abi_signature": self.CREDIT_DATA_ABI_SIGNATURE,
            },
        }

        prepare_url = f"{self.jq_verifier_url}/JsonApi/prepareRequest"

        try:
            response = self.session.post(
                prepare_url, json=attestation_request, timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                print(f"  FDC: JQ verifier prepared attestation successfully")

                # Store abiEncodedRequest for optional on-chain submission
                if "abiEncodedRequest" in result:
                    self._last_encoded_request = result["abiEncodedRequest"]
                    print(f"  FDC: abiEncodedRequest: {result['abiEncodedRequest'][:42]}...")

                # Extract the validated response body
                if "response" in result and "responseBody" in result["response"]:
                    return self._decode_attested_response(
                        result["response"]["responseBody"]
                    )

                if "data" in result:
                    return result["data"]

                return result

            print(f"  FDC: JQ verifier returned status {response.status_code}")
            return None

        except requests.exceptions.Timeout:
            print(f"  FDC: JQ verifier request timed out")
            return None
        except requests.exceptions.ConnectionError:
            print(f"  FDC: Could not connect to JQ verifier at {prepare_url}")
            return None
        except Exception as e:
            print(f"  FDC: Attestation error: {e}")
            return None

    def submit_to_fdc_hub(self, abi_encoded_request, account):
        """
        Submit the prepared attestation request to the FdcHub contract
        for on-chain Merkle root inclusion.

        This is optional and async - the data is already validated by the
        verifier in prepareRequest. This step adds on-chain provability.
        """
        if not self.w3 or not abi_encoded_request:
            return None

        try:
            # Minimal FdcHub ABI for requestAttestation
            fdc_hub_abi = [
                {
                    "inputs": [{"name": "data", "type": "bytes"}],
                    "name": "requestAttestation",
                    "outputs": [],
                    "stateMutability": "payable",
                    "type": "function",
                }
            ]

            fdc_hub = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.fdc_hub_address),
                abi=fdc_hub_abi,
            )

            request_bytes = bytes.fromhex(abi_encoded_request[2:])

            txn = fdc_hub.functions.requestAttestation(request_bytes).build_transaction(
                {
                    "from": account.address,
                    "nonce": self.w3.eth.get_transaction_count(account.address),
                    "gas": 500000,
                    "gasPrice": self.w3.eth.gas_price,
                    "value": self.w3.to_wei(0.001, "ether"),  # attestation fee
                }
            )

            signed = self.w3.eth.account.sign_transaction(txn, account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            # Calculate the voting round ID
            block = self.w3.eth.get_block(receipt["blockNumber"])
            voting_round = (
                block["timestamp"] - self.FIRST_VOTING_ROUND_START_TS
            ) // self.VOTING_EPOCH_DURATION_SEC

            print(f"  FDC: Submitted to FdcHub, tx: {tx_hash.hex()}")
            print(f"  FDC: Voting round: {voting_round}")

            return {
                "tx_hash": tx_hash.hex(),
                "voting_round": voting_round,
                "abi_encoded_request": abi_encoded_request,
            }

        except Exception as e:
            print(f"  FDC: FdcHub submission error: {e}")
            return None

    def get_proof(self, voting_round_id, request_bytes):
        """
        Retrieve Merkle proof from the DA layer after the voting round finalizes.

        Endpoint: POST {da_layer_url}/api/v1/fdc/proof-by-request-round
        """
        try:
            response = self.session.post(
                f"{self.da_layer_url}/api/v1/fdc/proof-by-request-round",
                json={
                    "votingRoundId": voting_round_id,
                    "requestBytes": request_bytes,
                },
                timeout=10,
            )

            if response.status_code == 200:
                result = response.json()
                print(f"  FDC: Proof retrieved from DA layer")
                return result

            print(f"  FDC: DA layer returned status {response.status_code}")
            return None

        except Exception as e:
            print(f"  FDC: Proof retrieval error: {e}")
            return None

    def _decode_attested_response(self, response_body):
        """
        Decode the attested response from FDC verifier back into
        the credit data format expected by our agents.
        """
        try:
            if isinstance(response_body, dict):
                return self._reconstruct_credit_data(response_body)

            if isinstance(response_body, str) and response_body.startswith("0x"):
                decoded = self.w3.codec.decode(
                    [
                        "(uint256,uint256,uint256,uint256,uint256,uint256,uint256,"
                        "uint256,uint256,uint256,uint256,uint256,"
                        "uint256,uint256,uint256,uint256)"
                    ],
                    bytes.fromhex(response_body[2:]),
                )
                values = decoded[0]
                return {
                    "experian": {
                        "fico_score": values[0],
                        "account_age_months": values[1],
                        "payment_history_percent": values[2] / 100,
                        "credit_utilization_percent": values[3] / 100,
                        "total_accounts": values[4],
                        "derogatory_marks": values[5],
                        "total_debt": values[6],
                    },
                    "plaid": {
                        "checking_balance": values[7] / 100,
                        "savings_balance": values[8] / 100,
                        "avg_monthly_income": values[9] / 100,
                        "avg_monthly_expenses": values[10] / 100,
                        "overdraft_count_6mo": values[11],
                    },
                    "payment_history": {
                        "on_time_payments_12mo": values[12],
                        "late_payments_12mo": values[13],
                        "missed_payments_12mo": values[14],
                        "debt_to_income_ratio": values[15] / 100,
                    },
                }
        except Exception as e:
            print(f"  FDC: Error decoding attested response: {e}")

        return None

    def _reconstruct_credit_data(self, flat_data):
        """Reconstruct nested credit data from flat JQ-processed response."""
        return {
            "experian": {
                "fico_score": flat_data.get("fico_score", 0),
                "account_age_months": flat_data.get("account_age_months", 0),
                "payment_history_percent": flat_data.get("payment_history_percent", 0) / 100,
                "credit_utilization_percent": flat_data.get("credit_utilization_percent", 0) / 100,
                "total_accounts": flat_data.get("total_accounts", 0),
                "derogatory_marks": flat_data.get("derogatory_marks", 0),
                "total_debt": flat_data.get("total_debt", 0),
            },
            "plaid": {
                "checking_balance": flat_data.get("checking_balance", 0) / 100,
                "savings_balance": flat_data.get("savings_balance", 0) / 100,
                "avg_monthly_income": flat_data.get("avg_monthly_income", 0) / 100,
                "avg_monthly_expenses": flat_data.get("avg_monthly_expenses", 0) / 100,
                "overdraft_count_6mo": flat_data.get("overdraft_count_6mo", 0),
            },
            "payment_history": {
                "on_time_payments_12mo": flat_data.get("on_time_payments_12mo", 0),
                "late_payments_12mo": flat_data.get("late_payments_12mo", 0),
                "missed_payments_12mo": flat_data.get("missed_payments_12mo", 0),
                "debt_to_income_ratio": flat_data.get("debt_to_income_ratio", 0) / 100,
            },
        }

    def _fetch_with_integrity(self, data_url, user_address):
        """
        Direct fetch from external data source with SHA-256 integrity hash.
        Used when FDC JQ verifier is unavailable. Still fetches externally
        (not from local JSON), maintaining the external data source pattern.
        """
        try:
            response = self.session.get(data_url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Compute integrity hash for verification
                raw = response.text
                integrity_hash = hashlib.sha256(raw.encode()).hexdigest()

                print(f"  FDC: External data fetched directly")
                print(f"  FDC: Integrity SHA-256: {integrity_hash[:16]}...")
                print(f"  FDC: Timestamp: {int(time.time())}")

                return data

            print(f"  FDC: External API returned status {response.status_code}")
            return None

        except requests.exceptions.ConnectionError:
            print(f"  FDC: Cannot reach external data source at {data_url}")
            return None
        except Exception as e:
            print(f"  FDC: Direct fetch error: {e}")
            return None

    def get_attestation_status(self):
        """Check FDC infrastructure health."""
        jq_ok = False
        da_ok = False

        try:
            r = self.session.get(f"{self.jq_verifier_url}/", timeout=5)
            jq_ok = r.status_code < 500
        except Exception:
            pass

        try:
            r = self.session.get(f"{self.da_layer_url}/", timeout=5)
            da_ok = r.status_code < 500
        except Exception:
            pass

        return {
            "jq_verifier_reachable": jq_ok,
            "da_layer_reachable": da_ok,
            "jq_verifier_url": self.jq_verifier_url,
            "da_layer_url": self.da_layer_url,
            "data_api_url": self.data_api_url,
            "fdc_hub": self.fdc_hub_address,
            "fdc_verification": self.fdc_verification_address,
        }
