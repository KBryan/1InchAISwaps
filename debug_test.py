#!/usr/bin/env python3
"""
Debug Test Script for Cross-Chain Swap Assistant
Helps identify and fix the mock transaction issues
"""

import requests
import json
import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_environment():
    """Check environment configuration"""
    print("🔍 Environment Check")
    print("=" * 30)

    required_vars = {
        "OPENAI_API_KEY": "OpenAI API for parsing",
        "ONEINCH_API_KEY": "1inch API for quotes",
        "PRIVATE_KEY": "Wallet private key (optional)",
    }

    all_good = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and len(value) > 10:  # Basic check for non-empty value
            print(f"✅ {var}: SET ({len(value)} chars)")
        else:
            print(f"❌ {var}: MISSING or EMPTY")
            print(f"   Purpose: {description}")
            all_good = False

    print()
    return all_good

def test_server_connection(base_url="http://localhost:8000"):
    """Test if server is running"""
    print("🌐 Server Connection Test")
    print("=" * 30)

    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Server is running")
            print(f"   Status: {data['status']}")
            print(f"   Version: {data['version']}")

            # Check service status
            services = data.get('services', {})
            print("\n📊 Service Status:")
            for service, status in services.items():
                print(f"   {service}: {status}")

            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("   Make sure the server is running: uvicorn app:app --reload")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_ai_parsing(base_url="http://localhost:8000"):
    """Test AI parsing specifically"""
    print("\n🤖 AI Parsing Test")
    print("=" * 30)

    test_input = "Swap 0.5 ETH to USDC on Ethereum"

    try:
        response = requests.post(
            f"{base_url}/test-ai-parser",
            json={"user_input": test_input},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ AI Parsing successful")
            print(f"   Input: {test_input}")

            result = data.get('parsed_result', {})
            print(f"   Parsed: {result.get('amount')} {result.get('from_token')} → {result.get('to_token')}")
            print(f"   Chains: {result.get('from_chain')} → {result.get('to_chain')}")

            if data.get('fallback_used'):
                print("⚠️  Used fallback parser (OpenAI API not available)")
            else:
                print("✅ Used OpenAI API")

            return True
        else:
            print(f"❌ AI parsing failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ AI parsing error: {e}")
        return False

def test_full_swap(base_url="http://localhost:8000"):
    """Test full swap process with detailed analysis"""
    print("\n🔄 Full Swap Test")
    print("=" * 30)

    test_cases = [
        "Swap 0.1 ETH to USDC on Ethereum",
        "Convert 0.001 BTC to ETH",
        "Exchange 50 USDC for MATIC on Polygon"
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_input}")
        print("-" * 40)

        try:
            response = requests.post(
                f"{base_url}/ai-swap",
                json={"user_input": test_input},
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()

                # Analyze the response
                print(f"✅ Status: {data.get('status')}")

                # Check parsed intent
                if data.get('parsed_intent'):
                    intent = data['parsed_intent']
                    print(f"🧠 Parsed: {intent['amount']} {intent['from_token']} → {intent['to_token']}")
                    print(f"🌐 Chains: {intent['from_chain']} → {intent['to_chain']}")

                # Check quote
                if data.get('quote'):
                    quote = data['quote']
                    print(f"💰 Output: {quote['estimated_output']}")
                    print(f"⛽ Gas: {quote['gas_estimate']}")
                    print(f"⏱️  Time: {quote['execution_time']}")

                    if quote.get('is_mock'):
                        print("⚠️  MOCK QUOTE (no 1inch API key)")
                    else:
                        print("✅ REAL QUOTE from 1inch API")

                # Check transaction
                if data.get('transaction'):
                    tx = data['transaction']
                    print(f"📋 TX Status: {tx['status']}")

                    if tx.get('hash'):
                        tx_hash = tx['hash']
                        print(f"🔗 Hash: {tx_hash[:20]}...")

                        # Analyze transaction hash
                        if is_mock_transaction_hash(tx_hash):
                            print("❌ MOCK TRANSACTION DETECTED")
                            print("   This is not a real blockchain transaction")
                        else:
                            print("✅ Looks like real transaction hash")

                    if tx.get('is_mock'):
                        print("⚠️  MOCK TRANSACTION (safety mode)")
                    else:
                        print("🚨 REAL TRANSACTION (would execute on blockchain)")

                # Check debug info
                if data.get('debug_info'):
                    debug = data['debug_info']
                    print(f"\n🐛 Debug Info:")
                    print(f"   Steps: {', '.join(debug.get('steps_completed', []))}")

                    warnings = debug.get('warnings', [])
                    if warnings:
                        print(f"   Warnings:")
                        for warning in warnings:
                            print(f"     - {warning}")

            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Error: {response.text}")

        except Exception as e:
            print(f"❌ Test error: {e}")

def is_mock_transaction_hash(tx_hash):
    """Detect if transaction hash is mock/fake"""
    if not tx_hash:
        return True

    # Common patterns in mock hashes
    mock_patterns = [
        "abcdef" * 10,  # Repeating pattern
        "1234567890" * 6,  # Sequential numbers
        "0x0000000000000000",  # All zeros
        "0xffffffffffffffff"   # All f's
    ]

    tx_hash_lower = tx_hash.lower()

    # Check for obvious patterns
    for pattern in mock_patterns:
        if pattern in tx_hash_lower:
            return True

    # Check for too much repetition
    if len(set(tx_hash_lower.replace('0x', ''))) < 8:  # Too few unique characters
        return True

    return False

def main():
    """Run all debug tests"""
    print("🚀 Cross-Chain Swap Debug Tool")
    print("=" * 50)
    print()

    # Step 1: Check environment
    env_ok = check_environment()

    # Step 2: Test server connection
    server_ok = test_server_connection()

    if not server_ok:
        print("\n❌ Cannot proceed - server is not running")
        print("\n🔧 To start the server:")
        print("   uvicorn app:app --reload")
        return

    # Step 3: Test AI parsing
    ai_ok = test_ai_parsing()

    # Step 4: Test full swap process
    test_full_swap()

    # Summary and recommendations
    print("\n" + "=" * 50)
    print("📊 SUMMARY & RECOMMENDATIONS")
    print("=" * 50)

    if not env_ok:
        print("\n🔧 ENVIRONMENT ISSUES:")
        print("1. Add your OpenAI API key to .env file")
        print("2. Get 1inch API key from https://portal.1inch.dev/")
        print("3. (Optional) Add wallet private key for real transactions")

    print("\n🎯 TO FIX MOCK TRANSACTIONS:")
    print("1. ✅ Use the fixed code versions provided")
    print("2. 🔑 Set up proper API keys in .env file")
    print("3. 🧪 Test with debug endpoints first")
    print("4. 🔄 Restart server after making changes")

    print("\n⚠️  SAFETY REMINDERS:")
    print("- Keep ENABLE_REAL_TRANSACTIONS=false for testing")
    print("- Use testnet for initial real transaction tests")
    print("- Never commit private keys to version control")
    print("- Monitor gas fees and slippage on mainnet")

    print(f"\n📖 Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    main()