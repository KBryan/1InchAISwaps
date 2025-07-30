"""
Cross-Chain Swap Assistant - Main FastAPI Application
AI-powered cross-chain swap service using 1inch Fusion+ protocol
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import os
from datetime import datetime
import asyncio

# Import our custom modules
from ai_parser import parse_swap_intent
from swap_service import OneinchService
from wallet import SimpleWallet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Cross-Chain Swap Assistant",
    description="Natural language powered cross-chain cryptocurrency swaps",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo purposes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response validation
class SwapRequest(BaseModel):
    """Request model for AI-powered swap operations"""
    user_input: str = Field(
        ..., 
        description="Natural language description of the desired swap",
        example="Swap 1 ETH to USDC on Arbitrum"
    )

class ParsedIntent(BaseModel):
    """Parsed swap intent from AI processing"""
    from_chain: str = Field(..., description="Source blockchain network")
    to_chain: str = Field(..., description="Destination blockchain network") 
    from_token: str = Field(..., description="Source token symbol")
    to_token: str = Field(..., description="Destination token symbol")
    amount: str = Field(..., description="Amount to swap")

class QuoteInfo(BaseModel):
    """Quote information from 1inch API"""
    estimated_output: str = Field(..., description="Estimated output amount")
    gas_estimate: str = Field(..., description="Estimated gas cost")
    execution_time: str = Field(..., description="Estimated execution time")
    price_impact: Optional[str] = Field(None, description="Price impact percentage")

class TransactionInfo(BaseModel):
    """Transaction execution information"""
    hash: Optional[str] = Field(None, description="Transaction hash")
    explorer_url: Optional[str] = Field(None, description="Blockchain explorer URL")
    status: str = Field(..., description="Transaction status")

class SwapResponse(BaseModel):
    """Response model for swap operations"""
    status: str = Field(..., description="Operation status")
    parsed_intent: Optional[ParsedIntent] = Field(None, description="AI-parsed swap parameters")
    quote: Optional[QuoteInfo] = Field(None, description="1inch quote information")
    transaction: Optional[TransactionInfo] = Field(None, description="Transaction details")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")

# Global variables for service instances (to be initialized)
oneinch_service = None
wallet = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    global oneinch_service, wallet
    
    logger.info("Starting Cross-Chain Swap Assistant...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize services (placeholder for now)
    logger.info("Services initialized successfully")

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic information"""
    return {
        "message": "AI Cross-Chain Swap Assistant",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
        version="1.0.0"
    )

@app.post("/ai-swap", response_model=SwapResponse)
async def ai_swap(request: SwapRequest):
    """
    Main endpoint for AI-powered cross-chain swaps
    
    This endpoint:
    1. Parses natural language input using AI
    2. Gets quotes from 1inch Fusion+ API
    3. Executes the swap transaction
    4. Returns comprehensive results
    """
    try:
        logger.info(f"Processing swap request: {request.user_input}")
        
        # Phase 1: AI Parsing
        parsed_intent_data = await parse_swap_intent(request.user_input)
        
        # Convert to Pydantic model
        parsed_intent = ParsedIntent(
            from_chain=parsed_intent_data["from_chain"],
            to_chain=parsed_intent_data["to_chain"],
            from_token=parsed_intent_data["from_token"],
            to_token=parsed_intent_data["to_token"],
            amount=parsed_intent_data["amount"]
        )
        
        # Phase 2: Get 1inch Quote
        async with OneinchService() as oneinch:
            quote_data = await oneinch.get_quote(
                from_token=parsed_intent.from_token,
                to_token=parsed_intent.to_token,
                amount=parsed_intent.amount,
                from_chain=parsed_intent.from_chain,
                to_chain=parsed_intent.to_chain
            )
        
        quote_info = QuoteInfo(
            estimated_output=quote_data["estimated_output"],
            gas_estimate=quote_data["gas_estimate"],
            execution_time=quote_data["execution_time"],
            price_impact=quote_data.get("price_impact")
        )
        
        # Phase 3: Execute Transaction
        wallet = SimpleWallet()
        
        if wallet.address:
            # Build transaction with 1inch
            async with OneinchService() as oneinch:
                tx_data = await oneinch.build_transaction(
                    quote_data=quote_data,
                    wallet_address=wallet.address,
                    from_token=parsed_intent.from_token,
                    to_token=parsed_intent.to_token,
                    amount=parsed_intent.amount,
                    from_chain=parsed_intent.from_chain
                )
            
            # Execute swap (mock for demo)
            transaction_result = await wallet.mock_execute_swap(tx_data, parsed_intent.from_chain)
            
            transaction_info = TransactionInfo(
                hash=transaction_result["transaction_hash"],
                explorer_url=transaction_result["explorer_url"],
                status=transaction_result["status"]
            )
        else:
            # No wallet configured - return mock transaction
            transaction_info = await mock_execute_swap(parsed_intent, quote_info)
        
        return SwapResponse(
            status="success",
            parsed_intent=parsed_intent,
            quote=quote_info,
            transaction=transaction_info
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Placeholder functions for development (to be replaced with actual implementations)

async def mock_parse_intent(user_input: str) -> ParsedIntent:
    """Mock AI parsing for development purposes"""
    # Simple keyword-based parsing for demo
    user_input_lower = user_input.lower()
    
    # Extract amount (simple regex would be better)
    amount = "1.0"
    if "0.1" in user_input:
        amount = "0.1"
    elif "0.5" in user_input:
        amount = "0.5"
    elif "100" in user_input:
        amount = "100"
    
    # Extract tokens
    from_token = "ETH"
    to_token = "USDC"
    
    if "btc" in user_input_lower:
        from_token = "BTC"
    if "matic" in user_input_lower:
        to_token = "MATIC"
    if "usdt" in user_input_lower:
        to_token = "USDT"
    
    # Extract chains
    from_chain = "ethereum"
    to_chain = "ethereum"
    
    if "arbitrum" in user_input_lower:
        to_chain = "arbitrum"
    if "polygon" in user_input_lower:
        to_chain = "polygon"
    
    return ParsedIntent(
        from_chain=from_chain,
        to_chain=to_chain,
        from_token=from_token,
        to_token=to_token,
        amount=amount
    )

async def mock_get_quote(parsed_intent: ParsedIntent) -> QuoteInfo:
    """Mock 1inch quote for development purposes"""
    # Simulate API delay
    await asyncio.sleep(0.1)
    
    # Mock quote calculation
    amount_float = float(parsed_intent.amount)
    if parsed_intent.from_token == "ETH" and parsed_intent.to_token == "USDC":
        estimated_output = str(amount_float * 2450.50)  # Mock ETH price
    else:
        estimated_output = str(amount_float * 1.0)  # Default 1:1 ratio
    
    return QuoteInfo(
        estimated_output=estimated_output,
        gas_estimate="0.002",
        execution_time="~2 minutes",
        price_impact="0.1%"
    )

async def mock_execute_swap(parsed_intent: ParsedIntent, quote_info: QuoteInfo) -> TransactionInfo:
    """Mock transaction execution for development purposes"""
    # Simulate transaction processing delay
    await asyncio.sleep(0.2)
    
    # Mock transaction hash
    mock_hash = "0x1234567890abcdef1234567890abcdef12345678"
    
    return TransactionInfo(
        hash=mock_hash,
        explorer_url=f"https://etherscan.io/tx/{mock_hash}",
        status="pending"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

