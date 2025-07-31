#!/usr/bin/env python3
"""
Robust Debug Script with Better Error Handling
Fixes the 'NoneType' object has no attribute 'get' error
"""

import requests
import json
import os
import traceback
from dotenv import load_dotenv

load_dotenv()

def test_with_detailed_debugging():
    """Test with comprehensive error handling and debugging"""
    print("🔧 Robust Debug Test - Cross-Chain Swap Assistant")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # Test 1: Basic server connectivity
    print("\n1️⃣  Server Connectivity Test")
    print("-" * 30)

    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Server Response Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('content-type', 'Unknown')}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   Message: {data.get('message', 'No message')}")
                print(f"   Version: {data.get('version', 'No version')}")
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"   Raw response: {response.text[:200]}...")
        else:
            print(f"❌ Server error. Raw response: {response.text[:200]}...")

    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server - is it running?")
        print("   Try: uvicorn app:app --reload")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    # Test 2: Health endpoint
    print("\n2️⃣  Health Check Test")
    print("-" * 30)

    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            try:
                health_data = response.json()
                print("✅ Health check successful")

                services = health_data.get('services', {})
                print("📊 Service Status:")
                for service, status in services.items():
                    print(f"   {service}: {status}")

            except json.JSONDecodeError as e:
                print(f"❌ Health JSON decode error: {e}")
        else:
            print(f"❌ Health check failed: {response.text[:200]}...")

    except Exception as e:
        print(f"❌ Health check error: {e}")

    # Test 3: AI Parser endpoint (should work now)
    print("\n3️⃣  AI Parser Test")
    print("-" * 30)

    try:
        test_payload = {"user_input": "Swap 0.1 ETH to USDC"}
        response = requests.post(
            f"{base_url}/test-ai-parser",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            try:
                parser_data = response.json()
                print("✅ AI Parser working")

                if parser_data and isinstance(parser_data, dict):
                    print(f"   Status: {parser_data.get('status', 'Unknown')}")

                    parsed_result = parser_data.get('parsed_result', {})
                    if parsed_result and isinstance(parsed_result, dict):
                        print(f"   Amount: {parsed_result.get('amount', 'Unknown')}")
                        print(f"   From: {parsed_result.get('from_token', 'Unknown')}")
                        print(f"   To: {parsed_result.get('to_token', 'Unknown')}")
                    else:
                        print(f"   ⚠️  Parsed result is not a dict: {type(parsed_result)}")
                else:
                    print(f"   ⚠️  Response data is not a dict: {type(parser_data)}")

            except json.JSONDecodeError as e:
                print(f"❌ AI Parser JSON error: {e}")
                print(f"   Raw response: {response.text[:500]}...")
        else:
            print(f"❌ AI Parser failed: {response.status_code}")
            print(f"   Error response: {response.text[:500]}...")

    except Exception as e:
        print(f"❌ AI Parser error: {e}")
        traceback.print_exc()

    # Test 4: Full swap test with detailed error handling
    print("\n4️⃣  Full Swap Test (Robust)")
    print("-" * 40)

    test_cases = [
        "Swap 0.01 ETH to USDC on Ethereum",
        "Convert 10 USDC to DAI"
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_input}")
        print("-" * 35)

        try:
            payload = {"user_input": test_input}
            print(f"   Sending payload: {payload}")

            response = requests.post(
                f"{base_url}/ai-swap",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=20
            )

            print(f"   Response Code: {response.status_code}")
            print(f"   Response Size: {len(response.content)} bytes")

            if response.status_code == 200:
                try:
                    # Try to parse JSON
                    data = response.json()
                    print(f"   ✅ JSON parsing successful")
                    print(f"   Data type: {type(data)}")

                    if data is None:
                        print("   ❌ Data is None!")
                        continue

                    if not isinstance(data, dict):
                        print(f"   ❌ Data is not a dict: {type(data)}")
                        print(f"   Data content: {str(data)[:200]}...")
                        continue

                    # Safe access to response fields
                    status = data.get('status', 'Unknown')
                    print(f"   📊 Status: {status}")

                    # Check parsed intent
                    parsed_intent = data.get('parsed_intent')
                    if parsed_intent and isinstance(parsed_intent, dict):
                        print(f"   🧠 Parsed: {parsed_intent.get('amount')} {parsed_intent.get('from_token')} → {parsed_intent.get('to_token')}")
                        print(f"   🌐 Chains: {parsed_intent.get('from_chain')} → {parsed_intent.get('to_chain')}")
                    else:
                        print(f"   ⚠️  Parsed intent issue: {type(parsed_intent)}")

                    # Check quote
                    quote = data.get('quote')
                    if quote and isinstance(quote, dict):
                        print(f"   💰 Output: {quote.get('estimated_output', 'Unknown')}")
                        print(f"   ⛽ Gas: {quote.get('gas_estimate', 'Unknown')}")
                        print(f"   🎭 Mock: {quote.get('is_mock', 'Unknown')}")
                    else:
                        print(f"   ⚠️  Quote issue: {type(quote)}")

                    # Check transaction
                    transaction = data.get('transaction')
                    if transaction and isinstance(transaction, dict):
                        tx_hash = transaction.get('hash', 'No hash')
                        execution_mode = transaction.get('execution_mode', 'unknown')
                        is_mock = transaction.get('is_mock', True)

                        print(f"   📋 TX Hash: {tx_hash[:20] if tx_hash else 'None'}...")
                        print(f"   🔧 Mode: {execution_mode}")
                        print(f"   🎭 Mock: {is_mock}")

                        # Analyze hash
                        if tx_hash and analyze_hash_quality(tx_hash):
                            print("   ✅ Hash looks realistic!")
                        else:
                            print("   ⚠️  Hash may be mock/invalid")
                    else:
                        print(f"   ⚠️  Transaction issue: {type(transaction)}")

                    # Check for errors in response
                    error = data.get('error')
                    if error:
                        print(f"   ❌ API Error: {error}")

                    # Check debug info
                    debug_info = data.get('debug_info')
                    if debug_info and isinstance(debug_info, dict):
                        execution_mode = debug_info.get('execution_mode', 'unknown')
                        warnings = debug_info.get('warnings', [])
                        steps = debug_info.get('steps_completed', [])

                        print(f"   🐛 Debug Mode: {execution_mode}")
                        print(f"   🔄 Steps: {len(steps)} completed")

                        if warnings:
                            print(f"   ⚠️  Warnings ({len(warnings)}):")
                            for warning in warnings[:2]:  # Show first 2
                                print(f"      • {warning}")
                    else:
                        print(f"   ⚠️  Debug info issue: {type(debug_info)}")

                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON decode error: {e}")
                    print(f"   Raw response preview: {response.text[:300]}...")

                except Exception as e:
                    print(f"   ❌ Response processing error: {e}")
                    traceback.print_exc()

            elif response.status_code == 422:
                print(f"   ❌ Validation error (422)")
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Raw error: {response.text}")

            elif response.status_code == 500:
                print(f"   ❌ Server error (500)")
                print(f"   This suggests a bug in the server code")
                print(f"   Raw response: {response.text[:500]}...")

            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                print(f"   Response: {response.text[:300]}...")

        except requests.exceptions.Timeout:
            print(f"   ❌ Request timeout (20s)")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection error")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            traceback.print_exc()

    # Test 5: Environment check
    print("\n5️⃣  Environment Analysis")
    print("-" * 30)

    env_vars = ["OPENAI_API_KEY", "ONEINCH_API_KEY", "PRIVATE_KEY"]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: SET ({len(value)} chars)")
        else:
            print(f"❌ {var}: NOT SET")

    # Summary
    print("\n" + "=" * 60)
    print("📊 DEBUG SUMMARY")
    print("=" * 60)

    print("\n🔍 Common Issues & Solutions:")
    print("1. Server not responding → Check if uvicorn is running")
    print("2. JSON decode errors → Check server logs for Python errors")
    print("3. 422 validation errors → Check request payload format")
    print("4. 500 server errors → Check server logs for exceptions")
    print("5. NoneType errors → API returning None/null values")

    print("\n🔧 Next Steps:")
    print("1. Check server logs: Look at the uvicorn output")
    print("2. Test individual endpoints: /health, /test-ai-parser")
    print("3. Verify fixed files are being used")
    print("4. Check for import errors in Python modules")

    print(f"\n📖 Server logs: Check your uvicorn terminal output")
    print(f"📋 API docs: {base_url}/docs")

def analyze_hash_quality(tx_hash: str) -> bool:
    """Analyze if a transaction hash looks realistic"""
    if not tx_hash or len(tx_hash) < 60:
        return False

    # Remove 0x prefix
    hash_part = tx_hash.replace('0x', '').lower()

    # Check for sufficient randomness
    unique_chars = len(set(hash_part))
    if unique_chars < 10:
        return False

    # Check for obvious patterns
    if 'abcdef' * 4 in hash_part:
        return False

    return True

if __name__ == "__main__":
    test_with_detailed_debugging()