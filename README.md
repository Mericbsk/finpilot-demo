# 🚀 FinPilot - AI-Powered Stock Analysis Platform

[![CI/CD](https://github.com/yourusername/finpilot/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/finpilot/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/finpilot/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/finpilot)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**FinPilot** is an intelligent stock scanning and analysis platform that combines technical analysis with AI-powered insights. Built for traders who want data-driven decisions.

![Dashboard Preview](docs/dashboard-preview.png)

## ✨ Features

- 📊 **Multi-Timeframe Analysis** - 15m, 1h, 4h, and daily trend alignment
- 🤖 **AI Financial Agent** - LLM-powered trading recommendations with master prompt system
- 🧠 **DRL Integration** - Deep Reinforcement Learning for adaptive strategies
- 📈 **Technical Indicators** - RSI, MACD, Bollinger Bands, EMA, ATR
- 🎯 **Signal Generation** - Automated entry/exit signals with risk management
- 📱 **Telegram Alerts** - Real-time notifications for trading signals
- 🛡️ **PilotShield Risk Controls** - Multi-layer risk management and position sizing

## 🏗️ Architecture

```
finpilot/
├── web/                  # Next.js frontend (local dev: http://localhost:3001)
├── api/                  # FastAPI backend (local dev: http://localhost:8000)
├── scanner/              # Technical scan and shortlist pipeline
├── drl/                  # DRL training, inference, registry, backtests
├── auth/                 # JWT auth, sessions, SQLite/PostgreSQL abstractions
├── core/                 # Config, cache, monitoring, logging
├── views/                # Legacy Streamlit UI surface (secondary)
├── tests/                # Unit and integration tests
└── scripts/              # Utility and admin tooling
```

## 📌 Runtime Contract

- **Tek resmi lokal geliştirme giriş noktası:** `bash start.sh`
- **Frontend local dev portu:** `3001`
- **Backend API portu:** `8000`
- **Liveness:** `/api/v1/health`
- **Readiness:** `/api/v1/ready`
- **Metrics:** `/api/v1/metrics`
- **Legacy Streamlit:** `streamlit_app.py` ve `views/` bakım amaçlı tutulur; birincil ürün yüzeyi değildir.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip or conda

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/finpilot.git
cd finpilot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running the Application

```bash
# Start the current local stack
bash start.sh

# Or via Makefile
make run

# Frontend
http://localhost:3001

# Backend
http://localhost:8000/api/v1/health
```

### Authentication Bootstrap

```bash
# Create an admin user for protected endpoints
python scripts/create_admin.py --email admin@finpilot.com --password SecurePass123!

# Login and obtain JWT tokens
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@finpilot.com","password":"SecurePass123!"}'
```

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# First-time setup for persistent local env vars
cp .env.example .env

# Build and run the current web + API stack
make docker-up

# View logs
make docker-logs

# Stop
make docker-down
```

Legacy Streamlit container is still present in `docker-compose.yml` as `finpilot`, but it is no longer the primary application entrypoint.

### Docker Smoke Test

```bash
# Builds, starts api+web, verifies ready/health/metrics + frontend, then tears down
make docker-smoke
```

If `.env` is missing, `make docker-smoke` creates a temporary local file with a throwaway secret just for the smoke run and removes it afterwards.

### Available Profiles

```bash
# Main app only
make docker-up

# Main app + legacy Streamlit
make docker-up-legacy

# With scanner service
docker compose --profile scanner up -d api web scanner

# With Telegram bot
docker compose --profile telegram up -d api web telegram_bot

# Full stack with Redis cache
make docker-full
```

For the legacy Streamlit surface outside Docker, use `make run-legacy`.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Required
GROQ_API_KEY=your_groq_api_key

# Optional - Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional - Data providers
POLYGON_API_KEY=your_polygon_key
```

### Scanner Settings

Edit `user_settings.json` for personalized settings:

```json
{
  "risk_score": 5,
  "portfolio_size": 10000,
  "strategy": "Normal",
  "market": "US"
}
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ --cov=scanner --cov=drl -v

# Run specific test file
pytest tests/test_indicators.py -v
```

## 📊 Scanner Module Usage

```python
from scanner import (
    add_indicators, fetch, load_symbols,
    check_volume_spike, analyze_price_momentum
)

# Fetch data with indicators
df = add_indicators(fetch('AAPL', '1d', 30))

# Check for signals
volume_spike = check_volume_spike(df)
momentum = analyze_price_momentum(df)

print(f"Volume Spike: {volume_spike}")
print(f"Momentum Bias: {momentum['momentum_bias']}")
```

## 🔧 Development

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Style

- **Formatter**: Black (line-length: 100)
- **Linter**: Ruff
- **Import Sorting**: isort

### Adding New Indicators

1. Add function to `scanner/indicators.py`
2. Export in `scanner/__init__.py`
3. Add tests to `tests/test_indicators.py`

## 📈 Roadmap

- [x] Modular scanner architecture
- [x] CI/CD pipeline
- [x] Docker deployment
- [x] Unit test coverage
- [ ] WebSocket real-time data
- [ ] Portfolio backtesting
- [ ] Mobile app
- [ ] Cloud deployment (AWS/Azure)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance data
- [Streamlit](https://streamlit.io/) - Dashboard framework
- [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) - RL algorithms
- [Groq](https://groq.com/) - Fast LLM inference

---

**Made with ❤️ for traders who code**
