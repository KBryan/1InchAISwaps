#!/usr/bin/env python3
"""
Test Real Transactions Script
Tests the fixed swap assistant to verify real transaction generation
"""

import requests
import json
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

def test_fixed_version():
    """Test the fixed version of the swap assistant"""
    print("🔧 Testing Fixed Cross-Chain Swap Assistant")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # Test 1: Check if server is running the fixed version
    print("\n1️⃣  Testing Server Version")
    print("-" * 30)

    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Server running: {data.get('message', 'Unknown')}")
            print(f"   Version: {data.get('version', 'Unknown')}")

            if "FINAL FIXED" in data.get('message', ''):
                print("🎉 FIXED VERSION DETECTED!")
            else:
                print("⚠️  May not be running fixed version")
        else:
            print(f"❌ Server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

    # Test 2: Check transaction modes endpoint
    print("\n2️⃣  Testing Transaction Modes")
    print("-" * 30)

    try:
        response = requests.get(f"{base_url}/debug/transaction-modes")
        if response.status_code == 200:
            data = response.json()
            config = data.get('current_configuration', {})

            print(f"🔑 Private Key: {'✅ Available' if config.get('has_private_key') else '❌ Missing'}")
            print(f"🔗 1inch API: {'✅ Available' if config.get('has_oneinch_key') else '❌ Missing'}")
            print(f"🚨 Real Mode: {'✅ Enabled' if config.get('real_transactions_enabled') else '❌ Disabled'}")

            print("\nExecution modes available:")
            for mode, description in data.get('modes_explained', {}).items():
                print(f"   {mode}: {description}")

        else:
            print(f"❌ Transaction modes check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Transaction modes error: {e}")

    # Test 3: Test AI Parser endpoint (this should work now)
    print("\n3️⃣  Testing AI Parser (Fixed)")
    print("-" * 30)

    try:
        response = requests.post(
            f"{base_url}/test-ai-parser",
            json={"user_input": "Swap 0.1 ETH to USDC"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ AI Parser endpoint working!")

            result = data.get('parsed_result', {})
            print(f"   Parsed: {result.get('amount')} {result.get('from_token')} → {result.get('to_token')}")

            if data.get('fallback_used'):
                print("   ⚠️  Used fallback parser (OpenAI API issues)")
            else:
                print("   ✅ Used OpenAI API successfully")
        else:
            print(f"❌ AI Parser failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ AI Parser error: {e}")

    # Test 4: Test full swap with real transaction detection
    print("\n4️⃣  Testing Full Swap (Real Transaction Detection)")
    print("-" * 50)

    test_swaps = [
        "Swap 0.01 ETH to USDC on Ethereum",
        "Convert 10 USDC to DAI"
    ]

    for i, swap_text in enumerate(test_swaps, 1):
        print(f"\n📝 Test {i}: {swap_text}")
        print("-" * 40)

        try:
            response = requests.post(
                f"{base_url}/ai-swap",
                json={"user_input": swap_text},
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()

                # Check quote
                quote = data.get('quote', {})
                print(f"💰 Quote: {quote.get('estimated_output')} (Mock: {quote.get('is_mock', 'Unknown')})")

                # Check transaction
                tx = data.get('transaction', {})
                if tx:
                    tx_hash = tx.get('hash', '')
                    execution_mode = tx.get('execution_mode', 'unknown')
                    is_mock = tx.get('is_mock', True)

                    print(f"📋 Transaction Hash: {tx_hash[:20]}...")
                    print(f"🔧 Execution Mode: {execution_mode}")
                    print(f"🎭 Is Mock: {is_mock}")

                    # Analyze hash quality
                    if analyze_transaction_hash(tx_hash):
                        print("✅ REAL-LOOKING TRANSACTION HASH!")
                    else:
                        print("❌ Still looks like mock hash")

                # Check debug info
                debug = data.get('debug_info', {})
                if debug:
                    warnings = debug.get('warnings', [])
                    execution_mode = debug.get('execution_mode', 'unknown')

                    print(f"🐛 Debug - Execution Mode: {execution_mode}")
                    if warnings:
                        print("⚠️  Warnings:")
                        for warning in warnings[:3]:  # Show first 3 warnings
                            print(f"     • {warning}")

            else:
                print(f"❌ Swap test failed: {response.status_code}")
                print(f"   Error: {response.text}")

        except Exception as e:
            print(f"❌ Swap test error: {e}")

    # Test 5: Recommendations
    print("\n" + "=" * 60)
    print("📋 RESULTS & NEXT STEPS")
    print("=" * 60)

    # Check if we can see improvement
    has_private_key = bool(os.getenv("PRIVATE_KEY"))
    has_oneinch_key = bool(os.getenv("ONEINCH_API_KEY"))
    real_mode = os.getenv("ENABLE_REAL_TRANSACTIONS", "false").lower() == "true"

    print(f"\n🔍 Current Configuration:")
    print(f"   Private Key: {'✅' if has_private_key else '❌'}")
    print(f"   1inch API Key: {'✅' if has_oneinch_key else '❌'}")
    print(f"   Real Transactions: {'✅' if real_mode else '❌'}")

    if has_private_key and has_oneinch_key:
        print(f"\n🎉 EXCELLENT! You should now see REAL transaction hashes!")
        print(f"   ✅ All API keys configured")
        print(f"   ✅ Wallet available for signing")

        if not real_mode:
            print(f"\n🚀 To enable FULL real transactions:")
            print(f"   1. Set ENABLE_REAL_TRANSACTIONS=true in .env")
            print(f"   2. Test on testnet first")
            print(f"   3. Monitor gas fees carefully")
    else:
        print(f"\n🔧 To get real transactions:")
        if not has_private_key:
            print(f"   • Add PRIVATE_KEY to .env file")
        if not has_oneinch_key:
            print(f"   • Add ONEINCH_API_KEY to .env file")
        print(f"   • Restart the server after changes")

    print(f"\n📖 More info: {base_url}/debug/transaction-modes")

def analyze_transaction_hash(tx_hash: str) -> bool:
    """Analyze if transaction hash looks realistic"""
    if not tx_hash or len(tx_hash) < 60:
        return False

    # Remove 0x prefix
    hash_part = tx_hash.replace('0x', '').lower()

    # Check for obvious mock patterns
    mock_patterns = ['abcdef' * 8, '123456' * 8, 'fedcba' * 8]
    for pattern in mock_patterns:
        if pattern[:20] in hash_part[:20]:  # Check first part
            return False

    # Check for sufficient randomness (at least 10 different characters)
    unique_chars = len(set(hash_part))
    if unique_chars < 10:
        return False

    return True

if __name__ == "__main__":
    test_fixed_version()