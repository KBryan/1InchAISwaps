#!/usr/bin/env python3
"""
Demo script for Cross-Chain Swap Assistant
Tests the API endpoints with sample requests
"""

import requests
import json
import time
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_health_endpoint(base_url="http://localhost:8000"):
    """Test the health check endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data['status']}")
            print(f"   Timestamp: {data['timestamp']}")
            print(f"   Version: {data['version']}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running with: uvicorn app:app --reload")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_ai_swap_endpoint(base_url="http://localhost:8000"):
    """Test the AI swap endpoint with various inputs"""
    print("\n🤖 Testing AI swap endpoint...")
    
    test_cases = [
        "Swap 1 ETH to USDC on Arbitrum",
        "Convert 0.1 BTC to ETH", 
        "Exchange 100 USDC for MATIC on Polygon",
        "Trade 0.5 ETH for USDT"
    ]
    
    for i, user_input in enumerate(test_cases, 1):
        print(f"\n📝 Test case {i}: '{user_input}'")
        
        try:
            response = requests.post(
                f"{base_url}/ai-swap",
                json={"user_input": user_input},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {data['status']}")
                
                if data.get('parsed_intent'):
                    intent = data['parsed_intent']
                    print(f"   🧠 AI Parsed: {intent['amount']} {intent['from_token']} → {intent['to_token']}")
                    print(f"   🌐 Chains: {intent['from_chain']} → {intent['to_chain']}")
                
                if data.get('quote'):
                    quote = data['quote']
                    print(f"   💰 Quote: {quote['estimated_output']} {intent['to_token']}")
                    print(f"   ⛽ Gas: {quote['gas_estimate']} ETH")
                    print(f"   ⏱️  Time: {quote['execution_time']}")
                
                if data.get('transaction'):
                    tx = data['transaction']
                    print(f"   📋 Transaction: {tx['status']}")
                    if tx.get('hash'):
                        print(f"   🔗 Hash: {tx['hash'][:20]}...")
                
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Test error: {e}")
        
        # Small delay between requests
        time.sleep(0.5)

def test_root_endpoint(base_url="http://localhost:8000"):
    """Test the root endpoint"""
    print("\n🏠 Testing root endpoint...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data['message']}")
            print(f"   Version: {data['version']}")
            print(f"   Docs: {base_url}{data['docs']}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def main():
    """Run all demo tests"""
    print("🚀 Cross-Chain Swap Assistant Demo")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test all endpoints
    health_ok = test_health_endpoint(base_url)
    root_ok = test_root_endpoint(base_url)
    
    if health_ok and root_ok:
        test_ai_swap_endpoint(base_url)
        print("\n✨ Demo completed! Check the results above.")
        print(f"\n📖 API Documentation: {base_url}/docs")
        print(f"🔄 ReDoc: {base_url}/redoc")
    else:
        print("\n❌ Basic endpoints failed. Please check server status.")
        print("\n🔧 To start the server:")
        print("   cd swap-assistant")
        print("   uvicorn app:app --reload")

if __name__ == "__main__":
    main()

