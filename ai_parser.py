"""
AI Parser Module for Cross-Chain Swap Assistant - FIXED VERSION
Uses OpenAI GPT-4 to parse natural language swap requests into structured parameters
"""

import json
import logging
import os
from typing import Dict, Any, Optional
import openai
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
)

# Supported tokens and chains configuration
SUPPORTED_TOKENS = {
    "ETH": {"name": "Ethereum", "decimals": 18, "chains": ["ethereum", "arbitrum", "polygon"]},
    "BTC": {"name": "Bitcoin", "decimals": 8, "chains": ["bitcoin", "ethereum"]},
    "USDC": {"name": "USD Coin", "decimals": 6, "chains": ["ethereum", "arbitrum", "polygon"]},
    "USDT": {"name": "Tether", "decimals": 6, "chains": ["ethereum", "arbitrum", "polygon"]},
    "MATIC": {"name": "Polygon", "decimals": 18, "chains": ["polygon", "ethereum"]},
    "ARB": {"name": "Arbitrum", "decimals": 18, "chains": ["arbitrum"]},
    "DAI": {"name": "Dai", "decimals": 18, "chains": ["ethereum", "arbitrum", "polygon"]},
}

SUPPORTED_CHAINS = {
    "ethereum": {"name": "Ethereum", "chain_id": 1, "native_token": "ETH"},
    "arbitrum": {"name": "Arbitrum One", "chain_id": 42161, "native_token": "ETH"},
    "polygon": {"name": "Polygon", "chain_id": 137, "native_token": "MATIC"},
    "bitcoin": {"name": "Bitcoin", "chain_id": 0, "native_token": "BTC"},
}

def create_parsing_prompt(user_input: str) -> str:
    """
    Create a sophisticated prompt for GPT-4 to parse swap requests
    """

    token_list = ", ".join(SUPPORTED_TOKENS.keys())
    chain_list = ", ".join(SUPPORTED_CHAINS.keys())

    prompt = f"""
You are an expert DeFi transaction parser. Parse the following natural language swap request into structured JSON parameters.

USER REQUEST: "{user_input}"

SUPPORTED TOKENS: {token_list}
SUPPORTED CHAINS: {chain_list}

PARSING RULES:
1. Extract the exact amount to swap (if not specified, use "1.0")
2. Identify source token (from_token) and destination token (to_token)
3. Determine source chain (from_chain) and destination chain (to_chain)
4. If chain is not specified, use "ethereum" as default
5. If only one chain is mentioned, use it for both source and destination
6. Handle common variations (e.g., "convert", "trade", "exchange" all mean "swap")
7. Normalize token symbols to uppercase
8. Normalize chain names to lowercase

RESPONSE FORMAT (JSON only, no explanation):
{{
    "from_chain": "ethereum",
    "to_chain": "arbitrum",
    "from_token": "ETH", 
    "to_token": "USDC",
    "amount": "1.0",
    "confidence": 0.95,
    "parsed_elements": {{
        "amount_found": true,
        "from_token_found": true,
        "to_token_found": true,
        "chain_specified": true
    }}
}}

EXAMPLES:
- "Swap 1 ETH to USDC on Arbitrum" → from_chain: "ethereum", to_chain: "arbitrum", from_token: "ETH", to_token: "USDC", amount: "1"
- "Convert 0.5 BTC to ETH" → from_chain: "bitcoin", to_chain: "ethereum", from_token: "BTC", to_token: "ETH", amount: "0.5"
- "Trade 100 USDC for MATIC on Polygon" → from_chain: "ethereum", to_chain: "polygon", from_token: "USDC", to_token: "MATIC", amount: "100"

Parse the user request now:
"""

    return prompt

async def parse_swap_intent(user_input: str) -> Dict[str, Any]:
    """
    Parse natural language swap request using OpenAI GPT-4

    Args:
        user_input: Natural language description of the swap

    Returns:
        Dictionary containing parsed swap parameters

    Raises:
        ValueError: If parsing fails or input is invalid
        Exception: If OpenAI API call fails
    """

    if not user_input or not user_input.strip():
        raise ValueError("Empty input provided")

    # Check if OpenAI API key is available
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("No OpenAI API key found, using fallback parser")
        return _fallback_parse_intent(user_input)

    try:
        logger.info(f"Parsing swap intent: {user_input}")

        # Create the parsing prompt
        prompt = create_parsing_prompt(user_input.strip())

        # Call OpenAI API with FIXED model name
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # FIXED: Use correct model name
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise DeFi transaction parser. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,  # Low temperature for consistent parsing
            max_tokens=500,
            timeout=30
        )

        # Extract and parse the response
        response_text = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response: {response_text}")

        # Handle markdown code blocks if present
        if response_text.startswith("```"):
            # Extract JSON from markdown code block
            lines = response_text.split('\n')
            json_lines = []
            in_code_block = False

            for line in lines:
                if line.startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block:
                    json_lines.append(line)

            response_text = '\n'.join(json_lines).strip()

        # Parse JSON response
        try:
            parsed_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text}")
            logger.warning("Falling back to simple parser")
            return _fallback_parse_intent(user_input)

        # Validate the parsed data
        validated_data = validate_parsed_intent(parsed_data, user_input)

        logger.info(f"Successfully parsed intent: {validated_data}")
        return validated_data

    except openai.APIError as e:
        logger.error(f"OpenAI API error: {e}")
        logger.warning("Falling back to simple parser")
        return _fallback_parse_intent(user_input)

    except openai.RateLimitError as e:
        logger.error(f"OpenAI rate limit exceeded: {e}")
        logger.warning("Falling back to simple parser")
        return _fallback_parse_intent(user_input)

    except Exception as e:
        logger.error(f"Unexpected error in AI parsing: {e}")
        logger.warning("Falling back to simple parser")
        return _fallback_parse_intent(user_input)

def _fallback_parse_intent(user_input: str) -> Dict[str, Any]:
    """
    Fallback parser when OpenAI API is unavailable
    Simple keyword-based parsing
    """
    user_input_lower = user_input.lower()

    # Extract amount using basic regex
    import re
    amount_match = re.search(r'(\d+\.?\d*)', user_input)
    amount = amount_match.group(1) if amount_match else "1.0"

    # Extract tokens
    from_token = "ETH"  # Default
    to_token = "USDC"   # Default

    tokens = ["ETH", "BTC", "USDC", "USDT", "MATIC", "ARB", "DAI"]
    found_tokens = []

    for token in tokens:
        if token.lower() in user_input_lower:
            found_tokens.append(token)

    if len(found_tokens) >= 2:
        from_token = found_tokens[0]
        to_token = found_tokens[1]
    elif len(found_tokens) == 1:
        to_token = found_tokens[0]

    # Extract chains
    from_chain = "ethereum"  # Default
    to_chain = "ethereum"    # Default

    if "arbitrum" in user_input_lower:
        to_chain = "arbitrum"
    elif "polygon" in user_input_lower:
        to_chain = "polygon"

    return {
        "from_chain": from_chain,
        "to_chain": to_chain,
        "from_token": from_token,
        "to_token": to_token,
        "amount": amount,
        "confidence": 0.6,  # Lower confidence for fallback
        "parsed_elements": {
            "amount_found": bool(amount_match),
            "from_token_found": len(found_tokens) > 0,
            "to_token_found": len(found_tokens) > 0,
            "chain_specified": any(chain in user_input_lower for chain in ["arbitrum", "polygon", "ethereum"])
        },
        "original_input": user_input,
        "fallback_used": True
    }

def validate_parsed_intent(parsed_data: Dict[str, Any], original_input: str) -> Dict[str, Any]:
    """
    Validate and normalize the parsed intent data

    Args:
        parsed_data: Raw parsed data from AI
        original_input: Original user input for context

    Returns:
        Validated and normalized intent data

    Raises:
        ValueError: If validation fails
    """

    required_fields = ["from_chain", "to_chain", "from_token", "to_token", "amount"]

    # Check required fields
    for field in required_fields:
        if field not in parsed_data:
            raise ValueError(f"Missing required field: {field}")

    # Validate and normalize tokens
    from_token = parsed_data["from_token"].upper()
    to_token = parsed_data["to_token"].upper()

    if from_token not in SUPPORTED_TOKENS:
        raise ValueError(f"Unsupported source token: {from_token}")

    if to_token not in SUPPORTED_TOKENS:
        raise ValueError(f"Unsupported destination token: {to_token}")

    # Validate and normalize chains
    from_chain = parsed_data["from_chain"].lower()
    to_chain = parsed_data["to_chain"].lower()

    if from_chain not in SUPPORTED_CHAINS:
        raise ValueError(f"Unsupported source chain: {from_chain}")

    if to_chain not in SUPPORTED_CHAINS:
        raise ValueError(f"Unsupported destination chain: {to_chain}")

    # Validate token-chain compatibility
    if from_chain not in SUPPORTED_TOKENS[from_token]["chains"]:
        raise ValueError(f"Token {from_token} not supported on chain {from_chain}")

    if to_chain not in SUPPORTED_TOKENS[to_token]["chains"]:
        raise ValueError(f"Token {to_token} not supported on chain {to_chain}")

    # Validate amount
    try:
        amount_float = float(parsed_data["amount"])
        if amount_float <= 0:
            raise ValueError("Amount must be positive")
        if amount_float > 1000000:  # Reasonable upper limit
            raise ValueError("Amount too large")
    except (ValueError, TypeError):
        raise ValueError(f"Invalid amount: {parsed_data['amount']}")

    # Check confidence if provided
    confidence = parsed_data.get("confidence", 0.8)
    if confidence < 0.7:
        logger.warning(f"Low confidence parsing ({confidence}) for input: {original_input}")

    # Return validated and normalized data
    return {
        "from_chain": from_chain,
        "to_chain": to_chain,
        "from_token": from_token,
        "to_token": to_token,
        "amount": str(amount_float),
        "confidence": confidence,
        "parsed_elements": parsed_data.get("parsed_elements", {}),
        "original_input": original_input,
        "fallback_used": parsed_data.get("fallback_used", False)
    }

def get_token_info(token_symbol: str) -> Optional[Dict[str, Any]]:
    """Get information about a supported token"""
    return SUPPORTED_TOKENS.get(token_symbol.upper())

def get_chain_info(chain_name: str) -> Optional[Dict[str, Any]]:
    """Get information about a supported chain"""
    return SUPPORTED_CHAINS.get(chain_name.lower())

def is_cross_chain_swap(from_chain: str, to_chain: str) -> bool:
    """Check if the swap is cross-chain"""
    return from_chain.lower() != to_chain.lower()

# Test function for development
async def test_parser():
    """Test the parser with sample inputs"""
    test_cases = [
        "Swap 1 ETH to USDC on Arbitrum",
        "Convert 0.1 BTC to ETH",
        "Exchange 100 USDC for MATIC on Polygon",
        "Trade 0.5 ETH for USDT",
        "Send 2 ETH to get DAI",
        "I want to swap my 50 USDC to ARB on Arbitrum"
    ]

    for test_input in test_cases:
        try:
            result = await parse_swap_intent(test_input)
            fallback_msg = " (FALLBACK)" if result.get("fallback_used") else ""
            print(f"✅ '{test_input}' → {result}{fallback_msg}")
        except Exception as e:
            print(f"❌ '{test_input}' → Error: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_parser())