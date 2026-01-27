# 🚀 FinPilot - AI-Powered Stock Analysis Platform

[![CI/CD](https://github.com/yourusername/finpilot/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/finpilot/actions/workflows/ci.yml)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**FinPilot** is an intelligent stock scanning and analysis platform that combines technical analysis with AI-powered insights. Built for traders who want data-driven decisions.

![Dashboard Preview](docs/dashboard-preview.png)

## ✨ Features

- 📊 **Multi-Timeframe Analysis** - 15m, 1h, 4h, and daily trend alignment
- 🤖 **AI Research Assistant** - Groq-powered market insights
- 📈 **Technical Indicators** - RSI, MACD, Bollinger Bands, EMA, ATR
- 🎯 **Signal Generation** - Automated entry/exit signals with risk management
- 📱 **Telegram Alerts** - Real-time notifications for trading signals
- 🔄 **DRL Integration** - Deep Reinforcement Learning for adaptive strategies

## 🏗️ Architecture

```
finpilot/
├── scanner/              # Modular scanning system
│   ├── indicators.py     # Technical indicators (EMA, RSI, MACD, etc.)
│   ├── signals.py        # Signal detection and scoring
│   ├── data_fetcher.py   # Market data retrieval
│   └── config.py         # Configuration management
├── drl/                  # Deep Reinforcement Learning
│   ├── market_env.py     # Gymnasium trading environment
│   ├── training.py       # Model training pipeline
│   └── data_loader.py    # Feature engineering
├── views/                # Streamlit dashboard views
├── tests/                # Unit and integration tests
└── scripts/              # Utility scripts
```

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
# Start Streamlit dashboard
streamlit run panel_new.py

# Run scanner
python scanner.py

# Run with aggressive mode
python scanner.py --aggressive
```

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f finpilot

# Stop
docker-compose down
```

### Available Profiles

```bash
# Main app only
docker-compose up -d

# With scanner service
docker-compose --profile scanner up -d

# With Telegram bot
docker-compose --profile telegram up -d

# Full stack with Redis cache
docker-compose --profile scanner --profile telegram --profile cache up -d
```

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
