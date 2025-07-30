"""
Wallet Module for Cross-Chain Swap Assistant
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
    Simple wallet implementation for transaction signing and blockchain interactions
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
    
    async def get_balance(self, chain: str, token_address: Optional[str] = None) -> Dict[str, Any]:
        """
        Get wallet balance for native token or ERC-20 token
        
        Args:
            chain: Chain name
            token_address: ERC-20 token address (None for native token)
            
        Returns:
            Balance information
        """
        if not self.address:
            raise ValueError("Wallet not initialized with private key")
        
        try:
            w3 = self.get_web3_connection(chain)
            
            if token_address is None or token_address == "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE":
                # Native token balance
                balance_wei = w3.eth.get_balance(self.address)
                balance_eth = w3.from_wei(balance_wei, 'ether')
                
                return {
                    "balance": str(balance_eth),
                    "balance_wei": str(balance_wei),
                    "token": "native",
                    "decimals": 18
                }
            else:
                # ERC-20 token balance
                # This is a simplified implementation - in production, you'd use the actual token ABI
                return await self._get_erc20_balance(w3, token_address)
                
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return {
                "balance": "0",
                "balance_wei": "0",
                "token": token_address or "native",
                "error": str(e)
            }
    
    async def _get_erc20_balance(self, w3: Web3, token_address: str) -> Dict[str, Any]:
        """Get ERC-20 token balance (simplified implementation)"""
        
        # Simplified ERC-20 ABI for balanceOf function
        erc20_abi = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]
        
        try:
            contract = w3.eth.contract(address=token_address, abi=erc20_abi)
            
            # Get balance and decimals
            balance_raw = contract.functions.balanceOf(self.address).call()
            decimals = contract.functions.decimals().call()
            
            # Convert to human-readable format
            balance = balance_raw / (10 ** decimals)
            
            return {
                "balance": str(balance),
                "balance_raw": str(balance_raw),
                "token": token_address,
                "decimals": decimals
            }
            
        except Exception as e:
            logger.error(f"Failed to get ERC-20 balance: {e}")
            return {
                "balance": "0",
                "balance_raw": "0",
                "token": token_address,
                "decimals": 18,
                "error": str(e)
            }
    
    async def estimate_gas(self, chain: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimate gas for a transaction
        
        Args:
            chain: Chain name
            transaction_data: Transaction parameters
            
        Returns:
            Gas estimation information
        """
        try:
            w3 = self.get_web3_connection(chain)
            
            # Prepare transaction for gas estimation
            tx_params = {
                'from': self.address or "0x0000000000000000000000000000000000000000",
                'to': transaction_data.get('to'),
                'data': transaction_data.get('data', '0x'),
                'value': int(transaction_data.get('value', '0'), 16) if isinstance(transaction_data.get('value'), str) else transaction_data.get('value', 0)
            }
            
            # Estimate gas
            gas_estimate = w3.eth.estimate_gas(tx_params)
            
            # Get current gas price
            gas_price = w3.eth.gas_price
            
            # Calculate total cost
            total_cost_wei = gas_estimate * gas_price
            total_cost_eth = w3.from_wei(total_cost_wei, 'ether')
            
            return {
                "gas_limit": gas_estimate,
                "gas_price": gas_price,
                "gas_price_gwei": w3.from_wei(gas_price, 'gwei'),
                "total_cost_wei": total_cost_wei,
                "total_cost_eth": str(total_cost_eth),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Gas estimation failed: {e}")
            
            # Return fallback estimates
            fallback_gas = int(transaction_data.get('gas', '250000'))
            fallback_gas_price = 20000000000  # 20 gwei
            
            return {
                "gas_limit": fallback_gas,
                "gas_price": fallback_gas_price,
                "gas_price_gwei": 20,
                "total_cost_wei": fallback_gas * fallback_gas_price,
                "total_cost_eth": str((fallback_gas * fallback_gas_price) / 10**18),
                "success": False,
                "error": str(e)
            }
    
    def sign_transaction(self, chain: str, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign a transaction
        
        Args:
            chain: Chain name
            transaction_data: Transaction parameters
            
        Returns:
            Signed transaction data
        """
        if not self.account:
            raise ValueError("Wallet not initialized with private key")
        
        try:
            w3 = self.get_web3_connection(chain)
            
            # Get current nonce
            nonce = w3.eth.get_transaction_count(self.address)
            
            # Prepare transaction
            tx_params = {
                'nonce': nonce,
                'to': transaction_data['to'],
                'value': int(transaction_data.get('value', '0'), 16) if isinstance(transaction_data.get('value'), str) else transaction_data.get('value', 0),
                'gas': int(transaction_data.get('gas', '250000')),
                'gasPrice': int(transaction_data.get('gasPrice', '20000000000')),
                'data': transaction_data.get('data', '0x'),
                'chainId': CHAIN_IDS.get(chain.lower(), 1)
            }
            
            # Sign transaction
            signed_txn = self.account.sign_transaction(tx_params)
            
            return {
                "signed_transaction": signed_txn.rawTransaction.hex(),
                "transaction_hash": signed_txn.hash.hex(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Transaction signing failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def broadcast_transaction(self, chain: str, signed_transaction: str) -> Dict[str, Any]:
        """
        Broadcast a signed transaction to the blockchain
        
        Args:
            chain: Chain name
            signed_transaction: Hex-encoded signed transaction
            
        Returns:
            Transaction broadcast result
        """
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
    
    async def wait_for_confirmation(
        self, 
        chain: str, 
        tx_hash: str, 
        confirmations: int = 1, 
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Wait for transaction confirmation
        
        Args:
            chain: Chain name
            tx_hash: Transaction hash
            confirmations: Number of confirmations to wait for
            timeout: Timeout in seconds
            
        Returns:
            Transaction confirmation status
        """
        try:
            w3 = self.get_web3_connection(chain)
            
            # Wait for transaction receipt
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            
            # Check if transaction was successful
            success = receipt.status == 1
            
            return {
                "success": success,
                "transaction_hash": tx_hash,
                "block_number": receipt.blockNumber,
                "gas_used": receipt.gasUsed,
                "status": "confirmed" if success else "failed",
                "receipt": dict(receipt)
            }
            
        except Exception as e:
            logger.error(f"Failed to wait for confirmation: {e}")
            return {
                "success": False,
                "error": str(e),
                "status": "timeout"
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
    
    # Mock functions for development without real blockchain access
    
    async def mock_execute_swap(
        self,
        transaction_data: Dict[str, Any],
        chain: str
    ) -> Dict[str, Any]:
        """
        Mock swap execution for development purposes
        
        Args:
            transaction_data: Transaction parameters from 1inch
            chain: Chain name
            
        Returns:
            Mock transaction execution result
        """
        
        # Simulate transaction processing delay
        await asyncio.sleep(0.5)
        
        # Generate mock transaction hash
        mock_hash = f"0x{''.join(['a', 'b', 'c', 'd', 'e', 'f'] * 10)[:64]}"
        
        return {
            "transaction_hash": mock_hash,
            "status": "pending",
            "explorer_url": self._get_explorer_url(chain, mock_hash),
            "gas_used": transaction_data.get('gas', '250000'),
            "success": True,
            "mock": True
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

# Test function
async def test_wallet():
    """Test wallet functionality"""
    
    print("🧪 Testing Wallet Functionality")
    
    # Test wallet creation
    new_wallet = generate_new_wallet()
    print(f"✅ Generated new wallet: {new_wallet['address']}")
    
    # Test wallet initialization
    wallet = SimpleWallet(new_wallet['private_key'])
    print(f"✅ Initialized wallet: {wallet.address}")
    
    # Test address validation
    valid = validate_address(wallet.address)
    print(f"✅ Address validation: {valid}")
    
    # Test mock swap execution
    mock_tx_data = {
        "to": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "data": "0x12345678",
        "value": "0",
        "gas": "250000"
    }
    
    result = await wallet.mock_execute_swap(mock_tx_data, "ethereum")
    print(f"✅ Mock swap execution: {result}")

if __name__ == "__main__":
    asyncio.run(test_wallet())

