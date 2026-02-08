import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Contract addresses
    ORACLE_ADDRESS = os.getenv('ORACLE_ADDRESS')
    LENDING_ADDRESS = os.getenv('LENDING_ADDRESS')
    TOKEN_ADDRESS = os.getenv('TOKEN_ADDRESS')

    # Network
    RPC_URL = os.getenv('RPC_URL')

    # Agent
    PRIVATE_KEY = os.getenv('PRIVATE_KEY')

    # Flare FDC (Data Connector) - Coston2 Testnet
    FDC_JQ_VERIFIER_URL = os.getenv(
        'FDC_JQ_VERIFIER_URL',
        'https://jq-verifier-test.flare.rocks'
    )
    FDC_DA_LAYER_URL = os.getenv(
        'FDC_DA_LAYER_URL',
        'https://ctn2-data-availability.flare.network'
    )
    FDC_DATA_API_URL = os.getenv(
        'FDC_DATA_API_URL',
        'http://localhost:8000/api/credit-data'
    )
    FDC_HUB_ADDRESS = os.getenv(
        'FDC_HUB_ADDRESS',
        '0x48aC463d7975828989331F4De43341627b9c5f1D'
    )
    FDC_VERIFICATION_ADDRESS = os.getenv(
        'FDC_VERIFICATION_ADDRESS',
        '0x075bf301fF07C4920e5261f93a0609640F53487D'
    )
    FDC_FEE_ADDRESS = os.getenv(
        'FDC_FEE_ADDRESS',
        '0x191a1282Ac700edE65c5B0AaF313BAcC3eA7fC7e'
    )
    FDC_API_KEY = os.getenv('FDC_API_KEY', '00000000-0000-0000-0000-000000000000')

    # Flare Secure RNG (RandomNumberV2) - Coston2 Testnet
    RANDOM_NUMBER_V2_ADDRESS = '0x5CdF9eAF3EB8b44fB696984a1420B56A7575D250'

    # Flare FTSO v2 (Price Feeds) - Coston2 Testnet
    FTSO_V2_ADDRESS = '0x3d893C53D9e8056135C26C8c638B76C8b60Df726'
    FTSO_FEED_FLR_USD = '0x01464c522f55534400000000000000000000000000'
    FTSO_FEED_XRP_USD = '0x015852502f55534400000000000000000000000000'

    # AWS Bedrock
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    BEDROCK_MODEL_ID = os.getenv(
        'BEDROCK_MODEL_ID',
        'global.anthropic.claude-sonnet-4-5-20250929-v1:0'
    )

    # Paths
    ORACLE_ABI_PATH = 'src/contracts/oracle_abi.json'
    LENDING_ABI_PATH = 'src/contracts/lending_abi.json'
    TOKEN_ABI_PATH = 'src/contracts/token_abi.json'

    @classmethod
    def validate(cls):
        """Validate all required config is present"""
        required = [
            'ORACLE_ADDRESS',
            'LENDING_ADDRESS',
            'TOKEN_ADDRESS',
            'RPC_URL',
            'PRIVATE_KEY'
        ]

        missing = [key for key in required if not getattr(cls, key)]

        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")
