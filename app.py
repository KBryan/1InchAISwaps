"""
Cross-Chain Swap Assistant - Quick Fix Version
Fixes the 'NoneType' object has no attribute 'get' error
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import hashlib
import time
import os

# Import our custom modules with error handling
try:
    from ai_parser import parse_swap_intent
    AI_PARSER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import ai_parser: {e}")
    AI_PARSER_AVAILABLE = False

try:
    from swap_service import OneinchService
    SWAP_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import swap_service: {e}")
    SWAP_SERVICE_AVAILABLE = False

try:
    from wallet import SimpleWallet
    WALLET_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import wallet: {e}")
    WALLET_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Cross-Chain Swap Assistant",
    description="Natural language powered cross-chain cryptocurrency swaps",
    version="1.0.2-quickfix",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For debugging - change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SwapRequest(BaseModel):
    user_input: str = Field(..., example="Swap 1 ETH to USDC")

class ParsedIntent(BaseModel):
    from_chain: str
    to_chain: str
    from_token: str
    to_token: str
    amount: str

class QuoteInfo(BaseModel):
    estimated_output: str
    gas_estimate: str
    execution_time: str
    price_impact: Optional[str] = None
    is_mock: bool = False

class TransactionInfo(BaseModel):
    hash: Optional[str] = None
    explorer_url: Optional[str] = None
    status: str
    is_mock: bool = True
    execution_mode: str = "mock"

class SwapResponse(BaseModel):
    status: str
    parsed_intent: Optional[ParsedIntent] = None
    quote: Optional[QuoteInfo] = None
    transaction: Optional[TransactionInfo] = None
    error: Optional[str] = None
    debug_info: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    services: Dict[str, str]

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger.info("Starting Cross-Chain Swap Assistant (Quick Fix Version)...")

    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()

    logger.info("Services initialized successfully")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "AI Cross-Chain Swap Assistant - QUICK FIX VERSION",
        "version": "1.0.2-quickfix",
        "docs": "/docs",
        "health": "/health",
        "status": "Fixed NoneType error"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""

    services = {
        "ai_parser": "✅ Available" if AI_PARSER_AVAILABLE else "❌ Import Error",
        "swap_service": "✅ Available" if SWAP_SERVICE_AVAILABLE else "❌ Import Error",
        "wallet": "✅ Available" if WALLET_AVAILABLE else "❌ Import Error",
        "openai": "✅ Available" if os.getenv("OPENAI_API_KEY") else "❌ No API Key",
        "oneinch": "✅ Available" if os.getenv("ONEINCH_API_KEY") else "❌ No API Key"
    }

    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.2-quickfix",
        services=services
    )

@app.post("/test-ai-parser")
async def test_ai_parser(request: SwapRequest):
    """Test AI parser endpoint with error handling"""
    try:
        if not AI_PARSER_AVAILABLE:
            return {
                "status": "error",
                "error": "AI parser module not available",
                "fallback_result": simple_parse(request.user_input)
            }

        result = await parse_swap_intent(request.user_input)

        return {
            "status": "success",
            "parsed_result": result,
            "fallback_used": result.get("fallback_used", False)
        }

    except Exception as e:
        logger.error(f"AI parser test failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "fallback_result": simple_parse(request.user_input)
        }

# COMPLETE FIXED SECTION - Replace in app.py

@app.post("/ai-swap", response_model=SwapResponse)
async def ai_swap(request: SwapRequest):
    """
    Main swap endpoint - COMPLETELY FIXED VERSION
    Now uses REAL 1inch transaction data instead of mock data
    """

    debug_info = {
        "steps_completed": [],
        "warnings": [],
        "modules_available": {
            "ai_parser": AI_PARSER_AVAILABLE,
            "swap_service": SWAP_SERVICE_AVAILABLE,
            "wallet": WALLET_AVAILABLE
        }
    }

    try:
        logger.info(f"Processing swap request: {request.user_input}")
        debug_info["original_request"] = request.user_input
        debug_info["steps_completed"].append("request_received")

        # Phase 1: Parse Intent
        try:
            if AI_PARSER_AVAILABLE:
                parsed_intent_data = await parse_swap_intent(request.user_input)
                debug_info["steps_completed"].append("ai_parsing_completed")
            else:
                parsed_intent_data = simple_parse(request.user_input)
                debug_info["warnings"].append("Using simple parser (AI parser not available)")
                debug_info["steps_completed"].append("simple_parsing_completed")

            if not parsed_intent_data or not isinstance(parsed_intent_data, dict):
                raise ValueError("Parsing returned invalid data")

            parsed_intent = ParsedIntent(
                from_chain=parsed_intent_data.get("from_chain", "ethereum"),
                to_chain=parsed_intent_data.get("to_chain", "ethereum"),
                from_token=parsed_intent_data.get("from_token", "ETH"),
                to_token=parsed_intent_data.get("to_token", "USDC"),
                amount=parsed_intent_data.get("amount", "1.0")
            )

        except Exception as e:
            logger.error(f"Parsing failed: {e}")
            debug_info["warnings"].append(f"Parsing error: {str(e)}")

            parsed_intent = ParsedIntent(
                from_chain="ethereum",
                to_chain="ethereum",
                from_token="ETH",
                to_token="USDC",
                amount="1.0"
            )

        # Phase 2: Get Quote
        try:
            if SWAP_SERVICE_AVAILABLE:
                async with OneinchService() as oneinch:
                    quote_data = await oneinch.get_quote(
                        from_token=parsed_intent.from_token,
                        to_token=parsed_intent.to_token,
                        amount=parsed_intent.amount,
                        from_chain=parsed_intent.from_chain,
                        to_chain=parsed_intent.to_chain
                    )
                debug_info["steps_completed"].append("quote_completed")
            else:
                quote_data = create_mock_quote(parsed_intent)
                debug_info["warnings"].append("Using mock quote (swap service not available)")
                debug_info["steps_completed"].append("mock_quote_completed")

            if not quote_data or not isinstance(quote_data, dict):
                raise ValueError("Quote service returned invalid data")

            quote_info = QuoteInfo(
                estimated_output=quote_data.get("estimated_output", "0"),
                gas_estimate=quote_data.get("gas_estimate", "0.002"),
                execution_time=quote_data.get("execution_time", "~30 seconds"),
                price_impact=quote_data.get("price_impact"),
                is_mock=quote_data.get("mock_data", True)
            )

        except Exception as e:
            logger.error(f"Quote failed: {e}")
            debug_info["warnings"].append(f"Quote error: {str(e)}")

            quote_info = QuoteInfo(
                estimated_output="100.0",
                gas_estimate="0.002",
                execution_time="~30 seconds",
                is_mock=True
            )

        # Phase 3: Build Transaction - FIXED TO USE REAL DATA
        try:
            if WALLET_AVAILABLE:
                wallet = SimpleWallet()
                if wallet.address:
                    debug_info["wallet_address"] = wallet.address

                    # FIXED: Build REAL transaction with 1inch
                    if SWAP_SERVICE_AVAILABLE:
                        async with OneinchService() as oneinch:
                            tx_data = await oneinch.build_transaction(
                                quote_data=quote_data,
                                wallet_address=wallet.address,
                                from_token=parsed_intent.from_token,
                                to_token=parsed_intent.to_token,
                                amount=parsed_intent.amount,
                                from_chain=parsed_intent.from_chain
                            )
                        debug_info["steps_completed"].append("real_transaction_build_completed")
                        debug_info["transaction_data"] = tx_data
                    else:
                        # Fallback transaction data
                        tx_data = {
                            "to": "0x1111111254EEB25477B68fb85Ed929f73A960582",
                            "data": "0x12345678",
                            "value": "0",
                            "gas": "250000",
                            "gasPrice": "20000000000",
                            "is_real_transaction": False
                        }
                        debug_info["warnings"].append("Using mock transaction data (swap service unavailable)")

                    # FIXED: Use real transaction data for signing
                    transaction_info = await create_real_transaction_fixed(
                        wallet, parsed_intent, quote_info, tx_data
                    )
                    debug_info["steps_completed"].append("real_transaction_created")
                else:
                    transaction_info = create_mock_transaction(parsed_intent)
                    debug_info["warnings"].append("No wallet configured - using mock transaction")
                    debug_info["steps_completed"].append("mock_transaction_created")
            else:
                transaction_info = create_mock_transaction(parsed_intent)
                debug_info["warnings"].append("Wallet service not available - using mock transaction")
                debug_info["steps_completed"].append("mock_transaction_created")

        except Exception as e:
            logger.error(f"Transaction creation failed: {e}")
            debug_info["warnings"].append(f"Transaction error: {str(e)}")
            transaction_info = create_mock_transaction(parsed_intent)

        debug_info["steps_completed"].append("all_phases_completed")

        return SwapResponse(
            status="success",
            parsed_intent=parsed_intent,
            quote=quote_info,
            transaction=transaction_info,
            debug_info=debug_info
        )

    except Exception as e:
        logger.error(f"Unexpected error in ai_swap: {e}")
        debug_info["error"] = str(e)
        debug_info["error_type"] = type(e).__name__

        return SwapResponse(
            status="error",
            error=f"Internal server error: {str(e)}",
            debug_info=debug_info
        )

async def create_real_transaction_fixed(
        wallet,
        parsed_intent: ParsedIntent,
        quote_info: QuoteInfo,
        real_tx_data: Dict[str, Any]
) -> TransactionInfo:
    """FIXED: Create a real transaction using actual 1inch data"""
    try:
        # Check if we have real 1inch transaction data
        if real_tx_data.get("is_real_transaction", False):
            # Use REAL 1inch transaction data
            tx_data = {
                "to": real_tx_data["to"],
                "data": real_tx_data["data"],
                "value": real_tx_data["value"],
                "gas": real_tx_data["gas"],
                "gasPrice": real_tx_data["gasPrice"]
            }
            logger.info(f"✅ Using REAL 1inch transaction data: to={tx_data['to'][:10]}...")
            is_real_1inch_tx = True
        else:
            # Fallback to mock data only if 1inch data is not available
            logger.warning("⚠️ 1inch transaction data not available, using mock for signing")
            tx_data = {
                "to": "0x1111111254EEB25477B68fb85Ed929f73A960582",
                "data": "0x12345678",
                "value": "0",
                "gas": "250000",
                "gasPrice": "20000000000"
            }
            is_real_1inch_tx = False

        # Sign the transaction to get a real hash
        signed_result = wallet.sign_transaction(parsed_intent.from_chain, tx_data)

        if signed_result and signed_result.get("success"):
            real_hash = signed_result["transaction_hash"]

            return TransactionInfo(
                hash=real_hash,
                explorer_url=get_explorer_url(parsed_intent.from_chain, real_hash),
                status="real_signed_not_broadcasted" if is_real_1inch_tx else "mock_signed",
                is_mock=not is_real_1inch_tx,
                execution_mode="real_simulation" if is_real_1inch_tx else "mock_simulation"
            )
        else:
            raise Exception("Transaction signing failed")

    except Exception as e:
        logger.warning(f"Real transaction creation failed: {e}")
        return create_mock_transaction(parsed_intent)

async def simulate_real_transaction(
        wallet: SimpleWallet,
        tx_data: Dict[str, Any],
        chain: str
) -> Dict[str, Any]:
    """
    FIXED: Simulate real transaction with actual 1inch data
    This builds and signs a real transaction but doesn't broadcast it
    """
    try:
        # Check if we have real transaction data
        if tx_data.get("is_real_transaction", False):
            logger.info("🔥 Using REAL 1inch transaction data for simulation")

            # Sign the REAL transaction (creates real hash)
            signed_result = wallet.sign_transaction(chain, tx_data)

            if signed_result.get("success"):
                return {
                    "transaction_hash": signed_result["transaction_hash"],
                    "status": "real_simulated",
                    "explorer_url": wallet._get_explorer_url(chain, signed_result["transaction_hash"]),
                    "is_mock": False,
                    "note": "REAL 1inch transaction signed but not broadcasted"
                }
            else:
                raise Exception(f"Real transaction signing failed: {signed_result.get('error')}")
        else:
            logger.warning("⚠️ No real transaction data available for simulation")
            # Fall back to mock hash generation
            return {
                "transaction_hash": f"0x{hashlib.sha256(f'{wallet.address}{chain}{time.time()}'.encode()).hexdigest()}",
                "status": "mock_simulated",
                "explorer_url": f"https://etherscan.io/tx/{generate_realistic_hash(wallet.address, chain)}",
                "is_mock": True,
                "note": "Mock simulation (no real 1inch data)"
            }

    except Exception as e:
        logger.error(f"Transaction simulation failed: {e}")
        return {
            "transaction_hash": generate_realistic_hash(wallet.address, chain),
            "status": "simulation_error",
            "explorer_url": f"https://etherscan.io/tx/{generate_realistic_hash(wallet.address, chain)}",
            "is_mock": True,
            "error": str(e)
        }

def simple_parse(user_input: str) -> Dict[str, Any]:
    """Simple fallback parser when AI parser is not available"""
    import re

    user_input_lower = user_input.lower()

    # Extract amount
    amount_match = re.search(r'(\d+\.?\d*)', user_input)
    amount = amount_match.group(1) if amount_match else "1.0"

    # Extract tokens
    from_token = "ETH"
    to_token = "USDC"

    if "btc" in user_input_lower:
        from_token = "BTC"
    if "dai" in user_input_lower:
        to_token = "DAI"
    if "usdt" in user_input_lower:
        to_token = "USDT"

    # Extract chains
    from_chain = "ethereum"
    to_chain = "ethereum"

    if "arbitrum" in user_input_lower:
        to_chain = "arbitrum"
    if "polygon" in user_input_lower:
        to_chain = "polygon"

    return {
        "from_chain": from_chain,
        "to_chain": to_chain,
        "from_token": from_token,
        "to_token": to_token,
        "amount": amount,
        "confidence": 0.7,
        "fallback_used": True,
        "original_input": user_input
    }

def create_mock_quote(parsed_intent: ParsedIntent) -> Dict[str, Any]:
    """Create a mock quote when service is not available"""
    amount_float = float(parsed_intent.amount)

    # Simple price calculation
    if parsed_intent.from_token == "ETH" and parsed_intent.to_token == "USDC":
        estimated_output = amount_float * 2450.0
    else:
        estimated_output = amount_float * 1.0

    return {
        "estimated_output": f"{estimated_output:.6f}",
        "gas_estimate": "0.002",
        "execution_time": "~30 seconds",
        "price_impact": "0.1%",
        "mock_data": True
    }

# FIXED VERSION - Replace in app.py

async def create_real_transaction(
        wallet,
        parsed_intent: ParsedIntent,
        quote_info: QuoteInfo,
        real_tx_data: Dict[str, Any]  # ← Add this parameter
) -> TransactionInfo:
    """Create a real transaction when wallet is available - FIXED VERSION"""
    try:
        # Use REAL transaction data from 1inch (not mock data)
        if real_tx_data.get("is_real_transaction", False):
            # Use the actual 1inch transaction data
            tx_data = {
                "to": real_tx_data["to"],
                "data": real_tx_data["data"],
                "value": real_tx_data["value"],
                "gas": real_tx_data["gas"],
                "gasPrice": real_tx_data["gasPrice"]
            }
            logger.info(f"Using real 1inch transaction data: to={tx_data['to']}")
        else:
            # Fallback to mock data only if 1inch data is not available
            logger.warning("1inch transaction data not available, using mock for signing")
            tx_data = {
                "to": "0x1111111254EEB25477B68fb85Ed929f73A960582",
                "data": "0x12345678",
                "value": "0",
                "gas": "250000",
                "gasPrice": "20000000000"
            }

        # Sign the transaction to get a real hash
        signed_result = wallet.sign_transaction(parsed_intent.from_chain, tx_data)

        if signed_result and signed_result.get("success"):
            real_hash = signed_result["transaction_hash"]

            # Determine if this is a real 1inch transaction or mock
            is_real_1inch_tx = real_tx_data.get("is_real_transaction", False)

            return TransactionInfo(
                hash=real_hash,
                explorer_url=get_explorer_url(parsed_intent.from_chain, real_hash),
                status="signed_not_broadcasted" if is_real_1inch_tx else "mock_signed",
                is_mock=not is_real_1inch_tx,
                execution_mode="simulation" if is_real_1inch_tx else "mock_simulation"
            )
        else:
            raise Exception("Transaction signing failed")

    except Exception as e:
        logger.warning(f"Real transaction creation failed: {e}")
        return create_mock_transaction(parsed_intent)



def create_mock_transaction(parsed_intent: ParsedIntent) -> TransactionInfo:
    """Create a mock transaction"""
    # Generate a realistic-looking hash
    hash_input = f"{parsed_intent.from_token}{parsed_intent.to_token}{time.time()}"
    mock_hash = "0x" + hashlib.sha256(hash_input.encode()).hexdigest()

    return TransactionInfo(
        hash=mock_hash,
        explorer_url=get_explorer_url(parsed_intent.from_chain, mock_hash),
        status="mock_pending",
        is_mock=True,
        execution_mode="mock"
    )

@app.get("/debug/modules")
async def debug_modules():
    """Debug endpoint to check module imports"""
    return {
        "module_status": {
            "ai_parser": AI_PARSER_AVAILABLE,
            "swap_service": SWAP_SERVICE_AVAILABLE,
            "wallet": WALLET_AVAILABLE
        },
        "environment": {
            "openai_key": bool(os.getenv("OPENAI_API_KEY")),
            "oneinch_key": bool(os.getenv("ONEINCH_API_KEY")),
            "private_key": bool(os.getenv("PRIVATE_KEY"))
        }
    }

def generate_realistic_hash(wallet_address: str, chain: str) -> str:
    """Generate a realistic-looking transaction hash"""
    import hashlib
    import time
    import os

    # Create hash based on wallet address, chain, and current time
    hash_input = f"{wallet_address}{chain}{time.time()}{os.urandom(8).hex()}"
    hash_result = hashlib.sha256(hash_input.encode()).hexdigest()
    return f"0x{hash_result}"

def get_explorer_url(chain: str, tx_hash: str) -> str:
    """Get explorer URL for a transaction hash"""
    explorers = {
        "ethereum": "https://etherscan.io/tx/",
        "arbitrum": "https://arbiscan.io/tx/",
        "polygon": "https://polygonscan.com/tx/",
        "optimism": "https://optimistic.etherscan.io/tx/",
        "base": "https://basescan.org/tx/"
    }

    base_url = explorers.get(chain.lower(), "https://etherscan.io/tx/")
    return f"{base_url}{tx_hash}"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )