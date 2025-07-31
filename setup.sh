#!/bin/bash

# Cross-Chain Swap Assistant Setup Script
echo "🚀 Cross-Chain Swap Assistant Setup"
echo "=================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.template .env
    echo "✅ Created .env file - please edit with your API keys"
else
    echo "✅ .env file already exists"
fi

# Check Python virtual environment
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
source .venv/bin/activate
pip install -r requirements.txt

echo ""
echo "🔧 Setup Complete! Next Steps:"
echo "=============================="
echo ""
echo "1. 📝 Edit the .env file with your API keys"
echo "2. 🚀 Start the server: uvicorn app:app --reload"
echo "3. 🧪 Test the fix: python test_real_transactions.py"
echo ""
echo "Happy swapping! 🔄"