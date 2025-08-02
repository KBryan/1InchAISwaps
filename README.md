
<img width="512" height="512" alt="nexusintent" src="https://github.com/user-attachments/assets/b452c9fb-4bc6-447f-ae05-51857928268d" />


# 🚀 Quick Reference Card

**Cross-Chain Swap Assistant - Essential Commands & API Usage**

## 🏃‍♂️ Quick Start (30 seconds)

```bash
# 1. Run automated setup
./setup.sh

# 2. Start server
./start_server.sh

# 3. Test API (in another terminal)
./test_api.sh
```

## 🔧 Essential Commands

### Server Management
```bash
# Start server
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Start with custom port
uvicorn app:app --reload --host 0.0.0.0 --port 3000

# Production mode
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing & Demo
```bash
# Health check
curl http://localhost:8000/health

# Basic demo
python3 demo/demo.py

# Full hackathon demo
python3 demo/hackathon_demo.py

# Quick demo (3 scenarios)
python3 demo/hackathon_demo.py --quick
```

## 🌐 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | System info |
| GET | `/health` | Health check |
| POST | `/ai-swap` | Main swap endpoint |
| GET | `/docs` | Interactive docs |

## 📝 API Usage Examples

### Basic Swap Request
```bash
curl -X POST "http://localhost:8000/ai-swap" \
     -H "Content-Type: application/json" \
     -d '{"user_input": "Swap 1 ETH to USDC on Arbitrum"}'
```

### Python Example
```python
import requests

response = requests.post("http://localhost:8000/ai-swap", 
    json={"user_input": "Swap 1 ETH to USDC on Arbitrum"})
print(response.json())
```

### JavaScript Example
```javascript
fetch('http://localhost:8000/ai-swap', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({user_input: 'Swap 1 ETH to USDC on Arbitrum'})
})
.then(r => r.json())
.then(console.log);
```

## 🎯 Natural Language Examples

### Cross-Chain Swaps
- `"Swap 1 ETH to USDC on Arbitrum"`
- `"Convert 0.1 BTC to ETH"`
- `"Exchange 100 USDC for MATIC on Polygon"`

### Conversational Style
- `"I want to trade my 0.5 ETH for some USDT please"`
- `"Can you swap 2 ETH to DAI?"`
- `"Trade 1000 USDC for ARB tokens"`

### Same-Chain Swaps
- `"Swap 1 ETH for USDT"`
- `"Convert 500 DAI to USDC"`
- `"Exchange ETH for 1000 USDT"`

## 🔑 Environment Variables

### Required
```env
OPENAI_API_KEY=sk-your-key-here
```

### Optional
```env
ONEINCH_API_KEY=your-1inch-key
PRIVATE_KEY=your-testnet-private-key
ETHEREUM_RPC_URL=your-rpc-endpoint
ARBITRUM_RPC_URL=your-arbitrum-rpc
POLYGON_RPC_URL=your-polygon-rpc
```

## 📊 Response Format

```json
{
  "status": "success",
  "parsed_intent": {
    "from_chain": "ethereum",
    "to_chain": "arbitrum",
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "1.0"
  },
  "quote": {
    "estimated_output": "2450.0",
    "gas_estimate": "0.005",
    "execution_time": "~2-5 minutes",
    "price_impact": "0.15%"
  },
  "transaction": {
    "hash": "0x...",
    "explorer_url": "https://etherscan.io/tx/0x...",
    "status": "pending"
  }
}
```

## 🌐 Supported Networks

| Network | Chain ID | Status |
|---------|----------|--------|
| Ethereum | 1 | ✅ |
| Arbitrum | 42161 | ✅ |
| Polygon | 137 | ✅ |
| Bitcoin | - | ✅ (Cross-chain) |

## 🪙 Supported Tokens

| Token | Networks | Type |
|-------|----------|------|
| ETH | Ethereum, Arbitrum | Native |
| BTC | Bitcoin → Others | Cross-chain |
| USDC | All | Stablecoin |
| USDT | All | Stablecoin |
| MATIC | Polygon | Native |
| DAI | Ethereum, Polygon | Stablecoin |
| ARB | Arbitrum | Governance |

## 🔧 Troubleshooting

### Common Issues
```bash
# Server won't start
pip3 install -r requirements.txt

# OpenAI API errors
echo $OPENAI_API_KEY  # Check key format

# Port already in use
lsof -ti:8000 | xargs kill -9

# Check server logs
tail -f server.log
```

### Debug Commands
```bash
# Test components individually
python3 -c "import asyncio; from ai_parser import test_ai_parser; asyncio.run(test_ai_parser())"
python3 -c "import asyncio; from swap_service import test_oneinch_service; asyncio.run(test_oneinch_service())"
python3 -c "import asyncio; from wallet import test_wallet; asyncio.run(test_wallet())"
```

## 📚 Documentation Links

- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Complete Tutorial**: [TUTORIAL.md](TUTORIAL.md)
- **Project README**: [README.md](README.md)
- **Project Summary**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## 🎬 Demo Commands

```bash
# Health check only
python3 demo/hackathon_demo.py --health

# Quick demo (3 scenarios)
python3 demo/hackathon_demo.py --quick

# Full demo (5 scenarios)
python3 demo/hackathon_demo.py

# Basic functionality test
python3 demo/demo.py
```

## 🚀 Production Deployment

```bash
# Using Gunicorn
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Using Docker
docker build -t swap-assistant .
docker run -p 8000:8000 --env-file .env swap-assistant
```

---

**💡 Pro Tips:**
- Always start with health check: `curl http://localhost:8000/health`
- Use interactive docs for testing: http://localhost:8000/docs
- Check server logs if issues occur: `tail -f server.log`
- Run demo scripts to verify functionality
- Keep your OpenAI API key secure and never commit to git

**🆘 Need Help?**
1. Check [TUTORIAL.md](TUTORIAL.md) for detailed instructions
2. Review [README.md](README.md) for complete documentation
3. Run `python3 demo/hackathon_demo.py --health` to verify setup
4. Check server logs for detailed error messages

