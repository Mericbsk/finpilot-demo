# 🎯 FinPilot: Kritik Eksiklikler Yol Planı

**Tarih:** 25 Ocak 2026
**Öncelik:** P0 - CRITICAL
**Tahmini Süre:** 6-8 Hafta

---

## 📋 DURUM ÖZETİ

### Mevcut Eksiklikler ve Etki Analizi

| Eksiklik | Mevcut Durum | İş Etkisi | Teknik Etki |
|----------|-------------|-----------|-------------|
| **DRL Training Pipeline** | %60 tamamlandı, live yok | AI avantajı kullanılamıyor | Model registry eksik |
| **Backtest Motoru** | Var ama entegre değil | Strateji doğrulaması zor | Dashboard bağlantısı yok |
| **User Authentication** | %0 - Yok | SaaS dönüşüm imkansız | Multi-tenant yok |
| **Real-time Data** | %10 - 15dk gecikmeli | Profesyonel kullanım zor | WebSocket yok |

---

## 🗓️ SPRINT PLANI

### SPRINT 1: DRL Training Pipeline Tamamlama (2 Hafta)

#### 1.1 Hedefler
- [ ] DRL modelini eğitebilir hale getir
- [ ] Model persistence ve loading
- [ ] Dashboard'a inference entegrasyonu

#### 1.2 Görevler

```
HAFTA 1: Core Training
├── Görev 1.1: Data loader tamamla (2 gün)
│   ├── drl/data_loader.py → fetch_training_data()
│   ├── Multi-symbol batch loading
│   └── Train/test split logic
│
├── Görev 1.2: Walk-forward splits oluştur (1 gün)
│   ├── create_walk_forward_splits()
│   ├── Configurable window sizes
│   └── Overlap handling
│
└── Görev 1.3: Training harness test et (2 gün)
    ├── PPO training loop
    ├── Hyperparameter tuning
    └── MLflow integration fix

HAFTA 2: Persistence & Inference
├── Görev 1.4: Model registry (2 gün)
│   ├── drl/model_registry.py (YENİ)
│   ├── save_model(), load_model()
│   ├── Version tagging
│   └── Best model selection
│
├── Görev 1.5: Live inference (2 gün)
│   ├── drl/inference.py (YENİ)
│   ├── predict_action(symbol, features)
│   ├── Batch prediction support
│   └── Confidence scoring
│
└── Görev 1.6: Dashboard entegrasyonu (1 gün)
    ├── views/dashboard.py → AI signals
    ├── DRL skorlarını UI'a ekle
    └── "AI Recommended" badge
```

#### 1.3 Deliverables

| Dosya | Açıklama | LOC (Tahmini) |
|-------|----------|---------------|
| `drl/data_loader.py` | Training data fetcher (tamamla) | +100 |
| `drl/model_registry.py` | Model persistence (YENİ) | ~150 |
| `drl/inference.py` | Live prediction (YENİ) | ~200 |
| `drl/training.py` | Fixes and enhancements | +50 |
| `views/dashboard.py` | DRL signals integration | +50 |

#### 1.4 Teknik Tasarım

```python
# drl/model_registry.py - Örnek API
class ModelRegistry:
    def __init__(self, storage_path: str = "models/"):
        self.storage_path = Path(storage_path)
        self.metadata_file = self.storage_path / "registry.json"

    def save_model(self, model, name: str, metrics: dict) -> str:
        """Model kaydet ve version ID döndür"""
        version_id = f"{name}_{datetime.now():%Y%m%d_%H%M%S}"
        model_path = self.storage_path / version_id
        model.save(model_path)
        self._update_registry(version_id, name, metrics)
        return version_id

    def load_best(self, name: str, metric: str = "sharpe") -> Any:
        """En iyi performanslı modeli yükle"""
        best = self._find_best(name, metric)
        return self._load_model(best["path"])

    def list_models(self, name: str = None) -> List[dict]:
        """Kayıtlı modelleri listele"""
        ...
```

```python
# drl/inference.py - Örnek API
class DRLInference:
    def __init__(self, model_registry: ModelRegistry):
        self.registry = model_registry
        self.model = None
        self.pipeline = None

    def load(self, model_name: str = "finpilot_ppo"):
        """En iyi modeli yükle"""
        self.model = self.registry.load_best(model_name)
        self.pipeline = self._load_pipeline(model_name)

    def predict(self, symbol: str, features: pd.DataFrame) -> dict:
        """Tek sembol için tahmin"""
        obs = self.pipeline.transform(features)
        action, _ = self.model.predict(obs, deterministic=True)
        return {
            "action": self._decode_action(action),
            "confidence": self._compute_confidence(action),
            "position_size": self._suggested_position(action)
        }

    def batch_predict(self, symbols: List[str]) -> pd.DataFrame:
        """Çoklu sembol tahmini"""
        ...
```

---

### SPRINT 2: Backtest Entegrasyonu (2 Hafta)

#### 2.1 Hedefler
- [ ] Mevcut backtest.py'yi modülerleştir
- [ ] Dashboard'a entegre et
- [ ] Equity curve ve performans grafikleri

#### 2.2 Görevler

```
HAFTA 3: Backtest Core Refactor
├── Görev 2.1: backtest/ paketi oluştur (2 gün)
│   ├── backtest/__init__.py
│   ├── backtest/engine.py
│   ├── backtest/metrics.py
│   └── backtest/report.py
│
├── Görev 2.2: Strategy abstraction (2 gün)
│   ├── backtest/strategies/base.py
│   ├── backtest/strategies/scanner_strategy.py
│   ├── backtest/strategies/drl_strategy.py
│   └── Strategy interface standardization
│
└── Görev 2.3: Data handling (1 gün)
    ├── Historical data caching
    ├── Corporate actions handling
    └── Survivorship bias mitigation

HAFTA 4: UI & Reporting
├── Görev 2.4: Performans metrikleri (2 gün)
│   ├── Sharpe Ratio, Sortino, Calmar
│   ├── Max Drawdown, Recovery Time
│   ├── Win Rate, Profit Factor
│   └── Monthly/Yearly returns
│
├── Görev 2.5: Görselleştirme (2 gün)
│   ├── Equity curve chart (Plotly)
│   ├── Drawdown chart
│   ├── Monthly heatmap
│   └── Trade distribution
│
└── Görev 2.6: Dashboard tab (1 gün)
    ├── views/backtest.py (YENİ)
    ├── Tab: "📈 Backtest Lab"
    ├── Strategy selector
    └── Date range picker
```

#### 2.3 Deliverables

| Dosya | Açıklama | LOC (Tahmini) |
|-------|----------|---------------|
| `backtest/__init__.py` | Package init | 30 |
| `backtest/engine.py` | Core backtest logic | 300 |
| `backtest/metrics.py` | Performance metrics | 150 |
| `backtest/report.py` | Report generation | 100 |
| `backtest/strategies/` | Strategy classes | 200 |
| `views/backtest.py` | UI tab (YENİ) | 250 |

#### 2.4 Teknik Tasarım

```python
# backtest/engine.py - Örnek API
class BacktestEngine:
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_capital: float = 10000,
        commission_bps: float = 10,
        slippage_bps: float = 15
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission_bps / 10000
        self.slippage = slippage_bps / 10000

    def run(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> BacktestResult:
        """Ana backtest döngüsü"""
        portfolio = Portfolio(self.initial_capital)
        trades = []

        for date in self._trading_days(start_date, end_date):
            signals = self.strategy.generate_signals(symbols, date)
            for signal in signals:
                if signal.action == "BUY":
                    trade = self._execute_buy(signal, portfolio, date)
                    trades.append(trade)
                elif signal.action == "SELL":
                    trade = self._execute_sell(signal, portfolio, date)
                    trades.append(trade)

            self._update_positions(portfolio, date)

        return BacktestResult(
            trades=trades,
            equity_curve=portfolio.equity_history,
            metrics=self._compute_metrics(portfolio)
        )

    def optimize(
        self,
        param_grid: dict,
        metric: str = "sharpe"
    ) -> OptimizationResult:
        """Parameter optimization via grid search"""
        ...
```

```python
# backtest/metrics.py - Performans hesaplamaları
def calculate_metrics(equity_curve: pd.Series, trades: List[Trade]) -> dict:
    returns = equity_curve.pct_change().dropna()

    return {
        # Risk-adjusted returns
        "sharpe_ratio": sharpe_ratio(returns),
        "sortino_ratio": sortino_ratio(returns),
        "calmar_ratio": calmar_ratio(equity_curve),

        # Drawdown metrics
        "max_drawdown": max_drawdown(equity_curve),
        "max_drawdown_duration": max_drawdown_duration(equity_curve),

        # Trade statistics
        "total_trades": len(trades),
        "win_rate": win_rate(trades),
        "profit_factor": profit_factor(trades),
        "avg_trade_pnl": avg_trade_pnl(trades),
        "avg_winner": avg_winner(trades),
        "avg_loser": avg_loser(trades),

        # Returns
        "total_return": total_return(equity_curve),
        "cagr": cagr(equity_curve),
        "volatility": returns.std() * np.sqrt(252)
    }
```

---

### SPRINT 3: User Authentication (2 Hafta)

#### 3.1 Hedefler
- [ ] Kullanıcı kayıt/giriş sistemi
- [ ] Session management
- [ ] Kullanıcı bazlı ayar kaydetme

#### 3.2 Görevler

```
HAFTA 5: Auth Backend
├── Görev 3.1: Supabase entegrasyonu (2 gün)
│   ├── auth/supabase_client.py
│   ├── Environment variables setup
│   └── User table schema
│
├── Görev 3.2: Auth service (2 gün)
│   ├── auth/service.py
│   ├── signup(), login(), logout()
│   ├── Password reset
│   └── Email verification
│
└── Görev 3.3: Session management (1 gün)
    ├── JWT token handling
    ├── Streamlit session integration
    └── Auto-logout on expiry

HAFTA 6: UI & User Features
├── Görev 3.4: Login/Signup UI (2 gün)
│   ├── views/auth.py (YENİ)
│   ├── Login form
│   ├── Signup form
│   └── Forgot password flow
│
├── Görev 3.5: User settings persistence (2 gün)
│   ├── DB schema for user_settings
│   ├── Sync with st.session_state
│   └── Watchlist per user
│
└── Görev 3.6: Protected routes (1 gün)
    ├── @require_auth decorator
    ├── Page access control
    └── Graceful redirect
```

#### 3.3 Deliverables

| Dosya | Açıklama | LOC (Tahmini) |
|-------|----------|---------------|
| `auth/__init__.py` | Package init | 20 |
| `auth/supabase_client.py` | DB connection | 80 |
| `auth/service.py` | Auth logic | 200 |
| `auth/decorators.py` | Access control | 50 |
| `views/auth.py` | Login/Signup UI | 250 |
| `views/profile.py` | User profile | 150 |

#### 3.4 Teknik Tasarım

```python
# auth/service.py - Örnek API
from supabase import create_client, Client

class AuthService:
    def __init__(self):
        self.client: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )

    def signup(self, email: str, password: str, name: str) -> dict:
        """Yeni kullanıcı kaydı"""
        response = self.client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"name": name}}
        })
        if response.user:
            self._create_user_profile(response.user.id, name)
        return {"success": True, "user_id": response.user.id}

    def login(self, email: str, password: str) -> dict:
        """Kullanıcı girişi"""
        response = self.client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return {
            "success": True,
            "user": response.user,
            "session": response.session
        }

    def get_current_user(self) -> Optional[User]:
        """Mevcut oturumu kontrol et"""
        return self.client.auth.get_user()

    def logout(self):
        """Oturumu sonlandır"""
        self.client.auth.sign_out()
```

```python
# auth/decorators.py - Route koruması
import streamlit as st
from functools import wraps

def require_auth(func):
    """Login gerektiren sayfalar için decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not st.session_state.get("authenticated"):
            st.warning("Bu sayfaya erişmek için giriş yapmalısınız.")
            st.switch_page("views/auth.py")
            return
        return func(*args, **kwargs)
    return wrapper

def require_premium(func):
    """Premium üyelik gerektiren özellikler için"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        user = st.session_state.get("user")
        if not user or not user.get("is_premium"):
            st.warning("Bu özellik Premium üyelere özeldir.")
            return
        return func(*args, **kwargs)
    return wrapper
```

---

### SPRINT 4: Real-time Data (2 Hafta) - OPSIYONEL

#### 4.1 Hedefler
- [ ] Polygon.io entegrasyonu
- [ ] WebSocket streaming
- [ ] Real-time price updates

#### 4.2 Görevler

```
HAFTA 7: Data Provider Migration
├── Görev 4.1: Polygon.io client (2 gün)
│   ├── data/polygon_client.py
│   ├── REST API wrapper
│   └── Rate limiting
│
├── Görev 4.2: Data abstraction layer (2 gün)
│   ├── data/provider.py (interface)
│   ├── data/yahoo_provider.py
│   ├── data/polygon_provider.py
│   └── Config-based provider selection
│
└── Görev 4.3: Historical data (1 gün)
    ├── Extended history (5+ years)
    ├── Intraday data (1min, 5min)
    └── Data quality checks

HAFTA 8: Real-time Streaming
├── Görev 4.4: WebSocket handler (2 gün)
│   ├── data/websocket_client.py
│   ├── Connection management
│   └── Reconnection logic
│
├── Görev 4.5: Live price updates (2 gün)
│   ├── views/live_ticker.py
│   ├── Price change animations
│   └── Alert triggers
│
└── Görev 4.6: Integration & testing (1 gün)
    ├── End-to-end testing
    ├── Fallback to delayed data
    └── Cost monitoring
```

#### 4.3 Maliyet Analizi

| Provider | Tier | Maliyet | Özellikler |
|----------|------|---------|------------|
| **yfinance** | Free | $0 | 15dk gecikme, rate limit |
| **Polygon.io** | Starter | $29/ay | Real-time, 5 calls/min |
| **Polygon.io** | Developer | $79/ay | Real-time, unlimited |
| **Alpha Vantage** | Free | $0 | 5 calls/min, 500/gün |
| **Finnhub** | Free | $0 | Real-time (limit var) |

**Öneri:** Polygon.io Starter ($29/ay) ile başla, kullanıcı sayısı artınca scale et.

---

## 📊 KAYNAK PLANI

### Tahmini Effort

| Sprint | Süre | Effort (saat) | Karmaşıklık |
|--------|------|---------------|-------------|
| Sprint 1: DRL | 2 hafta | 60-80 | Yüksek |
| Sprint 2: Backtest | 2 hafta | 50-70 | Orta |
| Sprint 3: Auth | 2 hafta | 40-60 | Orta |
| Sprint 4: Real-time | 2 hafta | 50-70 | Yüksek |
| **TOPLAM** | **8 hafta** | **200-280** | - |

### Bağımlılık Grafiği

```
                    ┌─────────────────┐
                    │  Sprint 1: DRL  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ Sprint 2:       │  │ Sprint 3:       │  │ Sprint 4:       │
    │ Backtest        │  │ Auth            │  │ Real-time       │
    │ (DRL Strategy)  │  │ (Independent)   │  │ (Independent)   │
    └─────────────────┘  └─────────────────┘  └─────────────────┘
              │                   │                    │
              └───────────────────┼────────────────────┘
                                  ▼
                    ┌─────────────────────────┐
                    │  Production Release     │
                    │  Version 3.0.0          │
                    └─────────────────────────┘
```

---

## ✅ BAŞARI KRİTERLERİ

### Sprint 1: DRL Training
- [ ] PPO model 1 sembol üzerinde eğitilebiliyor
- [ ] Model kaydedilip yüklenebiliyor
- [ ] Dashboard'da DRL skoru görünüyor
- [ ] Sharpe ratio > 0 (test seti)

### Sprint 2: Backtest
- [ ] Scanner stratejisi backtest edilebiliyor
- [ ] DRL stratejisi backtest edilebiliyor
- [ ] Equity curve grafiği çalışıyor
- [ ] 10+ metrik hesaplanıyor

### Sprint 3: Auth
- [ ] Kayıt ve giriş çalışıyor
- [ ] Ayarlar kullanıcıya bağlı
- [ ] Logout düzgün çalışıyor
- [ ] Şifre sıfırlama çalışıyor

### Sprint 4: Real-time
- [ ] Polygon.io bağlantısı kurulu
- [ ] Fiyatlar <5 saniyede güncelleniyor
- [ ] yfinance fallback çalışıyor
- [ ] Rate limiting yönetiliyor

---

## 🚀 HIZLI BAŞLANGIÇ

### İlk Adım: DRL Data Loader Tamamla

```bash
# 1. Mevcut durumu kontrol et
cd /workspaces/Borsa
python3 -c "from drl.data_loader import calculate_technical_features; print('OK')"

# 2. Requirements güncelle
pip install stable-baselines3[extra] shimmy

# 3. İlk training denemesi
python3 -c "
from drl.training import WalkForwardTrainer, WalkForwardConfig
from drl.config import MarketEnvConfig
print('Training module OK')
"
```

### Dosya Oluşturma Sırası

1. `drl/model_registry.py` → Model kaydetme/yükleme
2. `drl/inference.py` → Live tahmin
3. `backtest/__init__.py` → Package setup
4. `backtest/engine.py` → Core logic
5. `auth/__init__.py` → Auth package
6. `auth/service.py` → Auth logic

---

## 📁 YENİ DOSYA YAPISI (Hedef)

```
/workspaces/Borsa/
├── drl/
│   ├── ... (mevcut)
│   ├── model_registry.py   # YENİ
│   └── inference.py        # YENİ
│
├── backtest/               # YENİ PAKET
│   ├── __init__.py
│   ├── engine.py
│   ├── metrics.py
│   ├── report.py
│   └── strategies/
│       ├── __init__.py
│       ├── base.py
│       ├── scanner_strategy.py
│       └── drl_strategy.py
│
├── auth/                   # YENİ PAKET
│   ├── __init__.py
│   ├── supabase_client.py
│   ├── service.py
│   ├── decorators.py
│   └── models.py
│
├── data/                   # GENİŞLETİLMİŞ
│   ├── ... (mevcut)
│   ├── provider.py         # YENİ
│   ├── polygon_client.py   # YENİ
│   └── websocket_client.py # YENİ
│
├── views/
│   ├── ... (mevcut)
│   ├── backtest.py         # YENİ
│   ├── auth.py             # YENİ
│   └── profile.py          # YENİ
│
└── models/                 # YENİ - Model Storage
    └── registry.json
```

---

**Bu yol planı, FinPilot'u profesyonel bir ürüne dönüştürmek için gerekli kritik adımları tanımlamaktadır.**

**Önerilen başlangıç:** Sprint 1'e hemen başlayarak DRL training pipeline'ı tamamlamak.
