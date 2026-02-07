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
    
    # Paths (updated for src folder)
    MOCK_DATA_PATH = 'src/mock_data/credit_data.json'
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