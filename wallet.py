"""
Wallet Module for Cross-Chain Swap Assistant - FINAL FIXED VERSION
Handles wallet operations, transaction signing, and blockchain interactions
"""

import os
import logging
from typing import Dict, Any, Optional, Union
from decimal import Decimal
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
from web3.middleware import geth_poa_middleware
import asyncio
import hashlib
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# RPC endpoint configuration
RPC_ENDPOINTS = {
    "ethereum": os.getenv("ETHEREUM_RPC_URL", "https://eth-mainnet.g.alchemy.com/v2/demo"),
    "arbitrum": os.getenv("ARBITRUM_RPC_URL", "https://arb-mainnet.g.alchemy.com/v2/demo"),
    "polygon": os.getenv("POLYGON_RPC_URL", "https://polygon-mainnet.g.alchemy.com/v2/demo"),
    "optimism": os.getenv("OPTIMISM_RPC_URL", "https://opt-mainnet.g.alchemy.com/v2/demo"),
    "base": os.getenv("BASE_RPC_URL", "https://base-mainnet.g.alchemy.com/v2/demo")
}

# Chain ID mappings
CHAIN_IDS = {
    "ethereum": 1,
    "arbitrum": 42161,
    "polygon": 137,
    "optimism": 10,
    "base": 8453
}

class SimpleWallet:
    """
    Simple wallet implementation for transaction signing and blockchain interactions - FIXED VERSION
    """

    def __init__(self, private_key: Optional[str] = None):
        """
        Initialize wallet with private key

        Args:
            private_key: Hex-encoded private key (optional, will use env var if not provided)
        """
        self.private_key = private_key or os.getenv("PRIVATE_KEY")

        if not self.private_key:
            logger.warning("No private key provided - wallet will operate in read-only mode")
            self.account = None
            self.address = None
        else:
            try:
                # Remove '0x' prefix if present
                if self.private_key.startswith('0x'):
                    self.private_key = self.private_key[2:]

                # Create account from private key
                self.account: LocalAccount = Account.from_key(self.private_key)
                self.address = self.account.address
                logger.info(f"Wallet initialized with address: {self.address}")

            except Exception as e:
                logger.error(f"Failed to initialize wallet: {e}")
                self.account = None
                self.address = None

        # Web3 connections cache
        self._web3_connections: Dict[str, Web3] = {}


    def get_web3_connection(self, chain: str) -> Web3:
        """
        Get Web3 connection for a specific chain

        Args:
            chain: Chain name (e.g., 'ethereum', 'arbitrum')

        Returns:
            Web3 connection instance
        """
        chain_lower = chain.lower()

        if chain_lower not in self._web3_connections:
            rpc_url = RPC_ENDPOINTS.get(chain_lower)
            if not rpc_url:
                raise ValueError(f"No RPC endpoint configured for chain: {chain}")

            # Create Web3 connection
            w3 = Web3(Web3.HTTPProvider(rpc_url))

            # Add PoA middleware for chains that need it (like Polygon)
            if chain_lower in ["polygon", "arbitrum"]:
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)

            # Test connection
            try:
                if not w3.is_connected():
                    raise ConnectionError(f"Failed to connect to {chain} RPC")

                # Get chain ID to verify connection
                chain_id = w3.eth.chain_id
                expected_chain_id = CHAIN_IDS.get(chain_lower)

                if expected_chain_id and chain_id != expected_chain_id:
                    logger.warning(f"Chain ID mismatch for {chain}: got {chain_id}, expected {expected_chain_id}")

                logger.info(f"Connected to {chain} (Chain ID: {chain_id})")

            except Exception as e:
                logger.error(f"Failed to connect to {chain}: {e}")
                # For demo purposes, continue with the connection even if verification fails

            self._web3_connections[chain_lower] = w3

        return self._web3_connections[chain_lower]



    def sign_transaction(self, chain: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a transaction - FIXED VERSION

        Args:
            chain: Chain name
            transaction_data: Transaction parameters

        Returns:
            Signed transaction data with REAL hash
        """
        if not self.account:
            raise ValueError("Wallet not initialized with private key")

        try:
            w3 = self.get_web3_connection(chain)

            # Get current nonce
            nonce = w3.eth.get_transaction_count(self.address)

            # Prepare transaction with proper values
            tx_params = {
                'nonce': nonce,
                'to': w3.to_checksum_address(transaction_data['to']),
                'value': self._parse_value(transaction_data.get('value', '0')),
                'gas': max(250000, self._parse_gas(transaction_data.get('gas', '250000'))),
                'gasPrice': self._parse_gas_price(transaction_data.get('gasPrice', '20000000000')),
                'data': transaction_data.get('data', '0x'),
                'chainId': CHAIN_IDS.get(chain.lower(), 1)
            }

            logger.info(f"Signing transaction: {tx_params}")

            # Sign transaction
            signed_txn = self.account.sign_transaction(tx_params)

            # Generate REAL transaction hash
            real_tx_hash = signed_txn.hash.hex()

            logger.info(f"Transaction signed successfully: {real_tx_hash}")

            return {
                "signed_transaction": signed_txn.rawTransaction.hex(),
                "transaction_hash": real_tx_hash,  # This is a REAL hash now
                "success": True,
                "nonce": nonce,
                "chain_id": tx_params['chainId']
            }

        except Exception as e:
            logger.error(f"Transaction signing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _parse_value(self, value: Union[str, int]) -> int:
        """Parse value to integer"""
        if isinstance(value, str):
            if value.startswith('0x'):
                return int(value, 16)
            else:
                return int(value)
        return value

    def _parse_gas(self, gas: Union[str, int]) -> int:
        """Parse gas to integer"""
        if isinstance(gas, str):
            if gas.startswith('0x'):
                return int(gas, 16)
            else:
                return int(gas)
        return gas

    def _parse_gas_price(self, gas_price: Union[str, int]) -> int:
        """Parse gas price to integer"""
        if isinstance(gas_price, str):
            if gas_price.startswith('0x'):
                return int(gas_price, 16)
            else:
                return int(gas_price)
        return gas_price

    async def broadcast_transaction(self, chain: str, signed_transaction: str) -> Dict[str, Any]:
        """
        Broadcast a signed transaction to the blockchain

        Args:
            chain: Chain name
            signed_transaction: Hex-encoded signed transaction

        Returns:
            Transaction broadcast result
        """
        if not self.account:
            raise ValueError("Wallet not initialized")

        try:
            w3 = self.get_web3_connection(chain)

            # Broadcast transaction
            tx_hash = w3.eth.send_raw_transaction(signed_transaction)
            tx_hash_hex = tx_hash.hex()

            logger.info(f"Transaction broadcasted: {tx_hash_hex}")

            return {
                "transaction_hash": tx_hash_hex,
                "success": True,
                "explorer_url": self._get_explorer_url(chain, tx_hash_hex)
            }

        except Exception as e:
            logger.error(f"Transaction broadcast failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def execute_real_swap(
            self,
            transaction_data: Dict[str, Any],
            chain: str,
            broadcast: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a real swap transaction - NEW METHOD

        Args:
            transaction_data: Transaction parameters from 1inch
            chain: Chain name
            broadcast: Whether to actually broadcast to blockchain

        Returns:
            Real transaction execution result
        """

        if not self.account:
            raise ValueError("Wallet not initialized with private key")

        try:
            # Step 1: Sign the transaction (creates real hash)
            signed_result = self.sign_transaction(chain, transaction_data)

            if not signed_result.get("success"):
                raise Exception(f"Transaction signing failed: {signed_result.get('error')}")

            real_tx_hash = signed_result["transaction_hash"]

            if broadcast:
                # Step 2: Broadcast to blockchain (REAL execution)
                logger.warning("🚨 BROADCASTING REAL TRANSACTION TO BLOCKCHAIN")
                broadcast_result = await self.broadcast_transaction(
                    chain,
                    signed_result["signed_transaction"]
                )

                if broadcast_result.get("success"):
                    return {
                        "transaction_hash": real_tx_hash,
                        "status": "broadcasted",
                        "explorer_url": broadcast_result["explorer_url"],
                        "success": True,
                        "is_mock": False,
                        "execution_type": "real_blockchain"
                    }
                else:
                    raise Exception(f"Broadcast failed: {broadcast_result.get('error')}")
            else:
                # Step 2: Simulate (sign but don't broadcast)
                logger.info("📋 Transaction signed but not broadcasted (simulation mode)")
                return {
                    "transaction_hash": real_tx_hash,
                    "status": "signed_not_broadcasted",
                    "explorer_url": self._get_explorer_url(chain, real_tx_hash),
                    "success": True,
                    "is_mock": False,
                    "execution_type": "simulation",
                    "note": "Real transaction hash but not sent to blockchain"
                }

        except Exception as e:
            logger.error(f"Real swap execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_type": "failed"
            }

    def _get_explorer_url(self, chain: str, tx_hash: str) -> str:
        """Get blockchain explorer URL for transaction"""

        explorers = {
            "ethereum": "https://etherscan.io/tx/",
            "arbitrum": "https://arbiscan.io/tx/",
            "polygon": "https://polygonscan.com/tx/",
            "optimism": "https://optimistic.etherscan.io/tx/",
            "base": "https://basescan.org/tx/"
        }

        base_url = explorers.get(chain.lower(), "https://etherscan.io/tx/")
        return f"{base_url}{tx_hash}"

    # UPDATED Mock functions for compatibility

    async def mock_execute_swap(
            self,
            transaction_data: Dict[str, Any],
            chain: str
    ) -> Dict[str, Any]:
        """
        UPDATED Mock swap execution with better hash generation

        Args:
            transaction_data: Transaction parameters from 1inch
            chain: Chain name

        Returns:
            Enhanced mock transaction execution result
        """

        # Simulate transaction processing delay
        await asyncio.sleep(0.5)

        # Generate realistic mock hash based on actual data
        if self.address:
            hash_input = f"{self.address}{transaction_data.get('to', '')}{time.time()}"
        else:
            hash_input = f"mock{transaction_data.get('to', '')}{time.time()}"

        # Create hash that looks real but is clearly mock
        mock_hash = "0x" + hashlib.sha256(hash_input.encode()).hexdigest()

        return {
            "transaction_hash": mock_hash,
            "status": "mock_pending",
            "explorer_url": self._get_explorer_url(chain, mock_hash),
            "gas_used": transaction_data.get('gas', '250000'),
            "success": True,
            "is_mock": True,
            "execution_type": "mock",
            "note": "This is a mock transaction for testing purposes"
        }

# Utility functions

def generate_new_wallet() -> Dict[str, str]:
    """
    Generate a new wallet with private key and address

    Returns:
        Dictionary containing private key and address
    """
    account = Account.create()

    return {
        "private_key": account.key.hex(),
        "address": account.address,
        "mnemonic": None  # Could add mnemonic generation here
    }

def validate_address(address: str) -> bool:
    """
    Validate Ethereum address format

    Args:
        address: Ethereum address to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        return Web3.is_address(address)
    except Exception:
        return False

def validate_private_key(private_key: str) -> bool:
    """
    Validate private key format

    Args:
        private_key: Private key to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        if private_key.startswith('0x'):
            private_key = private_key[2:]

        # Check if it's a valid hex string of correct length
        if len(private_key) != 64:
            return False

        int(private_key, 16)  # This will raise ValueError if not valid hex

        # Try to create account to verify
        Account.from_key(private_key)
        return True

    except Exception:
        return False

# Test function with enhanced testing
async def test_wallet():
    """Test wallet functionality with real transaction signing"""

    print("🧪 Testing Wallet Functionality (Fixed Version)")

    # Test wallet creation
    new_wallet = generate_new_wallet()
    print(f"✅ Generated new wallet: {new_wallet['address']}")

    # Test wallet initialization with environment key
    wallet = SimpleWallet()
    if wallet.address:
        print(f"✅ Initialized wallet from env: {wallet.address}")

        # Test real transaction signing
        mock_tx_data = {
            "to": "0x1111111254EEB25477B68fb85Ed929f73A960582",
            "data": "0x12345678",
            "value": "0",
            "gas": "250000",
            "gasPrice": "20000000000"
        }

        print("\n📝 Testing transaction signing...")
        signed_result = wallet.sign_transaction("ethereum", mock_tx_data)

        if signed_result.get("success"):
            tx_hash = signed_result["transaction_hash"]
            print(f"✅ Real transaction signed: {tx_hash}")
            print(f"   Hash length: {len(tx_hash)} characters")
            print(f"   Starts with 0x: {tx_hash.startswith('0x')}")

            # Test realistic execution (no broadcast)
            print("\n🚀 Testing realistic execution...")
            exec_result = await wallet.execute_real_swap(mock_tx_data, "ethereum", broadcast=False)
            print(f"✅ Execution result: {exec_result}")

        else:
            print(f"❌ Transaction signing failed: {signed_result.get('error')}")
    else:
        print("⚠️  No wallet initialized (no private key in environment)")

        # Test with generated wallet
        test_wallet = SimpleWallet(new_wallet['private_key'])
        print(f"✅ Test wallet: {test_wallet.address}")

if __name__ == "__main__":
    asyncio.run(test_wallet())