"""
🧪 SADE BACKTEST SISTEM
Sistemimizin geçmiş performansını test eder
"""

import argparse
from datetime import datetime, timedelta
import warnings

import pandas as pd
import yfinance as yf

import scanner
from scanner import load_symbols, add_indicators, safe_float

warnings.filterwarnings('ignore')


def parse_args():
    parser = argparse.ArgumentParser(
        description="FinPilot basit backtest – z-skoru kalibrasyon karşılaştırmaları için CLI"
    )
    default_lookback = int(scanner.DEFAULT_SETTINGS.get("momentum_baseline_window", 60))
    default_dyn_window = int(scanner.DEFAULT_SETTINGS.get("momentum_dynamic_window", default_lookback))
    default_quantile = float(scanner.DEFAULT_SETTINGS.get("momentum_dynamic_quantile", 0.975))
    default_alpha = float(scanner.DEFAULT_SETTINGS.get("momentum_dynamic_alpha", 0.6))

    parser.add_argument("--start", type=str, help="Backtest başlangıç tarihi (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="Backtest bitiş tarihi (YYYY-MM-DD, dahil)")
    parser.add_argument(
        "--window-days",
        type=int,
        default=365,
        help="Başlangıç tarihi verilmezse, bitiş tarihinin bu kadar gün öncesi kullanılır."
    )
    parser.add_argument(
        "--portfolio",
        type=float,
        default=10000.0,
        help="Başlangıç portföy büyüklüğü."
    )
    parser.add_argument(
        "--risk",
        type=float,
        default=2.0,
        help="İşlem başına risk yüzdesi (örn. 2 = %%2)."
    )
    parser.add_argument(
        "--kelly",
        type=float,
        default=0.5,
        help="Kelly fraksiyonu (0.1 – 1.0 arası önerilir)."
    )
    parser.add_argument("--symbols", type=str, help="Virgülle ayrılmış sembol listesi (örn. AAPL,MSFT,NVDA)")

    parser.add_argument(
        "--lookback",
        type=int,
        default=default_lookback,
        help="Z-skoru ortalama ve standart sapma hesaplamasında kullanılacak pencere (gün)."
    )
    parser.add_argument(
        "--dynamic-window",
        type=int,
        default=default_dyn_window,
        help="Adaptif z-eşiği için rolling pencere uzunluğu (gün)."
    )
    parser.add_argument(
        "--quantile",
        type=float,
        default=default_quantile,
        help="Dinamik z-eşiği yüzdelik değeri (örn. 0.975 = %%97.5)."
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=default_alpha,
        help="Statik ve dinamik eşik karışımı için ağırlık (0-1 arası)."
    )
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Agresif eşik setini kullan (momentum filtreleri gevşetilir)."
    )
    parser.add_argument(
        "--dynamic",
        dest="dynamic",
        action="store_true",
        help="Dinamik z-eşiğini etkinleştir."
    )
    parser.add_argument(
        "--no-dynamic",
        dest="dynamic",
        action="store_false",
        help="Dinamik z-eşiğini devre dışı bırak."
    )
    parser.set_defaults(dynamic=bool(scanner.DEFAULT_SETTINGS.get("momentum_dynamic_enabled", True)))

    parser.add_argument(
        "--segment-presets",
        dest="segment_presets",
        action="store_true",
        help="Likidite segmentine göre z-eşiği preset'lerini kullan."
    )
    parser.add_argument(
        "--no-segment-presets",
        dest="segment_presets",
        action="store_false",
        help="Likidite preset'lerini devre dışı bırak."
    )
    parser.set_defaults(segment_presets=bool(scanner.DEFAULT_SETTINGS.get("momentum_segment_thresholds")))

    return parser.parse_args()


def resolve_symbols(args):
    if args.symbols:
        parts = [part.strip().upper() for part in args.symbols.split(",")]
        symbols = [p for p in parts if p]
        if symbols:
            return symbols
    return load_symbols()


def configure_scanner_settings(args):
    settings = scanner.DEFAULT_SETTINGS.copy()
    if args.aggressive:
        overrides = scanner.AGGRESSIVE_OVERRIDES.copy()
        settings.update(overrides)

    settings["momentum_baseline_window"] = max(5, int(args.lookback))
    settings["momentum_dynamic_enabled"] = bool(args.dynamic)
    dyn_window = max(int(args.dynamic_window), settings["momentum_baseline_window"])
    settings["momentum_dynamic_window"] = dyn_window
    settings["momentum_dynamic_quantile"] = float(args.quantile)
    settings["momentum_dynamic_alpha"] = float(args.alpha)

    if args.segment_presets:
        presets = scanner.DEFAULT_SETTINGS.get("momentum_segment_thresholds", {}).copy()
    else:
        presets = {}
    settings["momentum_segment_thresholds"] = presets

    scanner.SETTINGS = settings
    return settings

class SimpleBacktest:
    def __init__(self, start_portfolio=10000.0, risk_per_trade=2.0, commission_bps=5.0, slippage_bps=10.0, kelly_fraction=0.5):
        self.start_portfolio = start_portfolio
        self.current_portfolio = start_portfolio
        self.risk_percent = risk_per_trade
        self.kelly_fraction = kelly_fraction  # Modifiye Kelly fraksiyonu (örn. 0.5 = yarım Kelly)
        self.commission_bps = float(commission_bps)  # ör. 5 bps = %0.05
        self.slippage_bps = float(slippage_bps)      # ör. 10 bps = %0.10
        self.trades = []
        self.daily_portfolio = []
        self.data_cache = {}
        self.signals_found = 0
        self.momentum_logs = []
        self.debug_counts = {
            'simulate_calls': 0,
            'df_missing': 0,
            'slice_short': 0,
            'score_rsi': 0,
            'score_vol': 0,
            'score_macd': 0,
            'filt_vol': 0,
            'filt_mom': 0,
            'filt_trend': 0,
            'entry_true': 0,
            'exceptions': 0
        }
        self.index_data = None
        self.index_symbol = None

    def load_index_data(self, symbols, start_date, end_date):
        """Piyasa endeks verisini yükler (Regime Filter için)"""
        # Endeks belirle
        if any(s.endswith('.IS') for s in symbols):
            self.index_symbol = 'XU100.IS'
        elif any(s.endswith('.DE') for s in symbols):
            self.index_symbol = '^GDAXI' # DAX Performance Index
        else:
            self.index_symbol = '^IXIC' # NASDAQ Composite
            
        print(f"📊 Piyasa Endeksi Yükleniyor: {self.index_symbol}")
        
        try:
            # Biraz geriden al ki EMA200 hesaplanabilsin
            start_dt = datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=365)
            df_index = yf.download(self.index_symbol, start=start_dt, end=end_date, progress=False)
            
            if df_index is not None and not df_index.empty:
                # EMA 200 ve EMA 50 hesapla
                df_index['ema200'] = df_index['Close'].ewm(span=200, adjust=False).mean()
                df_index['ema50'] = df_index['Close'].ewm(span=50, adjust=False).mean()
                self.index_data = df_index
                print(f"✅ Endeks verisi hazır: {len(df_index)} gün")
            else:
                print("⚠️ Endeks verisi indirilemedi!")
        except Exception as e:
            print(f"⚠️ Endeks yükleme hatası: {e}")

    def check_market_regime(self, date):
        """Piyasa genel trendini kontrol eder (Index Filter)"""
        if self.index_data is None:
            return True # Veri yoksa filtre uygulama
            
        try:
            target_ts = pd.Timestamp(date)
            # get_indexer yerine get_loc kullan (daha güvenli scalar dönüşü için)
            # Ancak get_loc method='nearest' destekler mi? Evet, DatetimeIndex için destekler.
            try:
                idx_arr = self.index_data.index.get_indexer([target_ts], method='nearest')
                idx_loc = int(idx_arr[0])
            except:
                # Fallback
                return True
                
            data_date = pd.Timestamp(self.index_data.index[idx_loc])
            
            # Timestamp farkı
            diff = target_ts - data_date
            if abs(diff.days) > 3:
                return True
                
            row = self.index_data.iloc[idx_loc]
            
            close_val = float(row['Close'])
            open_val = float(row['Open'])
            ema_val = float(row['ema50']) # EMA50 kullan (Daha sıkı filtre)
            
            # 1. Trend Filtresi: Fiyat EMA50'nin altında ise işlem yapma
            if close_val < ema_val:
                return False 
                
            # 2. Momentum Filtresi (Red Day): Endeks günü ekside kapattıysa işlem yapma
            # Bu, "düşen bıçak" günlerini (31 Temmuz gibi) engeller.
            if close_val < open_val:
                return False
                
            return True # Yükseliş trendi ve Yeşil Mum -> Güvenli
            
        except Exception:
            return True

    def validate_symbols(self, symbols):
        """Yahoo'da günlük verisi olan sembolleri filtreler (hızlı kontrol)."""
        valid = []
        for sym in symbols:
            try:
                tkr = yf.Ticker(sym)
                df = tkr.history(period="6mo", interval="1d", auto_adjust=True, actions=False)
                if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                    if 'Close' in df.columns and df['Close'].notna().sum() >= 30:
                        valid.append(sym)
            except Exception:
                continue
        return valid
        
    def backtest_period(self, symbols, start_date, end_date):
        """Belirli dönemde backtest yap"""
        print(f"🧪 Backtest başlıyor: {start_date} - {end_date}")
        print(f"💰 Başlangıç portföy: ${self.start_portfolio:,.2f}")
        print("⏳ Test ediliyor...")
        
        # Günlük kontrol için tarih aralığı
        current_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")

        # Evreni doğrula (verisi olanları tut)
        print("🔎 Sembol doğrulama (6 ay veri kontrolü)...")
        symbols_valid = self.validate_symbols(symbols)
        
        # Endeks verisini yükle
        self.load_index_data(symbols_valid, start_date, end_date)

        print(f"✅ Geçerli semboller: {len(symbols_valid)}/{len(symbols)}")

        # Hız için veri önbelleği (sembol başına tek indirme)
        print("📦 Veri önbelleği hazırlanıyor...")
        fail_reasons = {}
        sample_symbol = None
        for sym in symbols_valid:
            try:
                tkr = yf.Ticker(sym)
                df = tkr.history(period="400d", interval="1d", auto_adjust=True, prepost=False, actions=False, back_adjust=False)
                if df is None or df.empty:
                    fail_reasons[sym] = 'empty'
                    continue
                if 'Close' not in df.columns and 'Adj Close' in df.columns:
                    df = df.rename(columns={'Adj Close': 'Close'})
                needed = {"Open", "High", "Low", "Close", "Volume"}
                if not needed.issubset(set(df.columns)):
                    fail_reasons[sym] = f"missing_cols:{list(df.columns)}"
                    continue
                try:
                    if isinstance(df.index, pd.DatetimeIndex) and getattr(df.index, 'tz', None) is not None:
                        df.index = df.index.tz_convert(None)
                except Exception:
                    pass
                df = df.dropna()
                if len(df) < 120:  # lowered threshold
                    fail_reasons[sym] = f"short:{len(df)}"
                    continue
                df = add_indicators(df)
                if df is None or not isinstance(df, pd.DataFrame) or df.empty:
                    fail_reasons[sym] = 'ind_failed'
                    continue
                self.data_cache[sym] = df
                if sample_symbol is None:
                    sample_symbol = sym
            except Exception as e:
                fail_reasons[sym] = f"ex:{type(e).__name__}"
                continue
        print(f"✅ Önbelleğe alınan sembol sayısı: {len(self.data_cache)}/{len(symbols_valid)}")
        try:
            if self.data_cache:
                lens = [len(d) for d in self.data_cache.values()]
                print(f"ℹ️ Önbellek uzunlukları (min/avg/max): {min(lens)}/{sum(lens)//len(lens)}/{max(lens)}")
                any_sym = next(iter(self.data_cache))
                any_df = self.data_cache[any_sym]
                first_idx = any_df.index[0] if len(any_df) > 0 else 'N/A'
                last_idx = any_df.index[-1] if len(any_df) > 0 else 'N/A'
                print(f"ℹ️ Örnek {any_sym} tarih aralığı: {str(first_idx)[:10]} → {str(last_idx)[:10]}")
                if sample_symbol and sample_symbol in self.data_cache:
                    samp_df = self.data_cache[sample_symbol].tail(3)
                    cols = ['Close','ema50','ema200','rsi','macd_hist','atr','vol_med20']
                    print(f"ℹ️ Örnek indikatör satırları ({sample_symbol}):")
                    try:
                        print(samp_df[cols])
                    except Exception:
                        print(samp_df.head())
            else:
                # Show up to 5 fail reasons for debugging
                shown = 0
                for k, v in fail_reasons.items():
                    print(f"[cache-fail] {k}: {v}")
                    shown += 1
                    if shown >= 5:
                        break
        except Exception:
            pass
        
        while current_date <= end_date_obj:
            date_str = current_date.strftime("%Y-%m-%d")
            self.check_signals_for_date(list(self.data_cache.keys()), date_str)
            # Günlük portföy değerini kaydet (step-function)
            self.daily_portfolio.append({
                'date': date_str,
                'portfolio_value': self.current_portfolio
            })
            current_date += timedelta(days=1)
            
        self.calculate_results()
        
    def check_signals_for_date(self, symbols, date):
        """Belirli günde sinyalleri kontrol et"""
        # Market Regime Filter (Global)
        if not self.check_market_regime(date):
            return

        for symbol in symbols:
            try:
                # O günkü durumu simüle et
                df_full = self.data_cache.get(symbol)
                result = self.simulate_signal_for_date(symbol, date, df_full)
                if result and result.get('entry_ok', False):
                    self.signals_found += 1
                    self.execute_trade(symbol, result, date)
            except Exception:
                continue
                
    def simulate_signal_for_date(self, symbol, date, df_full=None):
        """Belirli tarih için sinyal simülasyonu"""
        try:
            self.debug_counts['simulate_calls'] += 1
            # O tarihe kadar olan verileri al
            end_date = datetime.strptime(date, "%Y-%m-%d")
            start_date = end_date - timedelta(days=400)  # Yeterli veri için

            if df_full is None:
                # Veri çek (fallback)
                df = yf.download(symbol, start=start_date.strftime("%Y-%m-%d"), 
                               end=end_date.strftime("%Y-%m-%d"), progress=False)
                if df is None or not isinstance(df, pd.DataFrame) or df.empty or len(df) < 250:
                    self.debug_counts['df_missing'] += 1
                    return None
                df = add_indicators(df)
            else:
                df = df_full

            # O güne kadar olan kısmı al
            if isinstance(df.index, pd.DatetimeIndex):
                end_ts = pd.Timestamp(end_date)
                df_slice = df.loc[df.index <= end_ts]
            else:
                df_slice = df

            if df_slice.empty or len(df_slice) < 30:
                self.debug_counts['slice_short'] += 1
                return None
                
            # Temel kontroller
            last_row = df_slice.iloc[-1]
            
            # Trend kontrolü (200 EMA) - SIKI MOD
            regime = safe_float(last_row['Close']) > safe_float(last_row['ema200'])
            
            # Yön kontrolü (50 EMA) - SIKI MOD
            direction = safe_float(last_row['Close']) > safe_float(last_row['ema50'])
            
            # Basit sinyal skoru
            score = 0
            if len(df_slice) >= 2:
                prev_row = df_slice.iloc[-2]
                
                # RSI sinyali (Metindeki kural: 30-70 arası)
                if 30 <= safe_float(last_row['rsi']) <= 70:
                    self.debug_counts['score_rsi'] += 1
                    score += 1
                    
                # Volume sinyali (Metindeki kural: Ortalamadan %20 fazla)
                if safe_float(last_row['Volume']) > safe_float(last_row['vol_med20']) * 1.2:
                    self.debug_counts['score_vol'] += 1
                    score += 1
                    
                # MACD sinyali (Metindeki kural: Pozitif ve Artan)
                # Histogram > 0 (Pozitif bölge) VE Histogram > Önceki (Artışta)
                if safe_float(last_row['macd_hist']) > 0 and safe_float(last_row['macd_hist']) > safe_float(prev_row['macd_hist']):
                    self.debug_counts['score_macd'] += 1
                    score += 1
            
            momentum_analysis = None
            telemetry_record = {
                'symbol': symbol,
                'date': date,
                'positive': False,
                'dominant_z': None,
                'dominant_horizon': None,
                'dominant_return_pct': None,
                'threshold_effective': None,
                'threshold_base': None,
                'threshold_dynamic': None,
                'liquidity_segment': None,
                'dynamic_samples': None,
            }
            try:
                momentum_analysis = scanner.analyze_price_momentum(df_slice)
            except Exception:
                momentum_analysis = None

            if momentum_analysis:
                price_momentum = bool(momentum_analysis.get('positive'))
                telemetry_record['positive'] = price_momentum
                try:
                    telemetry_record['dominant_z'] = float(momentum_analysis.get('dominant_zscore'))
                except (TypeError, ValueError):
                    telemetry_record['dominant_z'] = None
                telemetry_record['dominant_horizon'] = momentum_analysis.get('best', {}).get('horizon') if momentum_analysis.get('best') else None
                try:
                    telemetry_record['dominant_return_pct'] = float(momentum_analysis.get('dominant_return_pct'))
                except (TypeError, ValueError):
                    telemetry_record['dominant_return_pct'] = None
                for key_src, key_dst in [
                    ('z_threshold_effective', 'threshold_effective'),
                    ('z_threshold_base', 'threshold_base'),
                    ('z_threshold_dynamic', 'threshold_dynamic'),
                ]:
                    telemetry_record[key_dst] = momentum_analysis.get(key_src)
                telemetry_record['liquidity_segment'] = momentum_analysis.get('liquidity_segment')
                telemetry_record['dynamic_samples'] = momentum_analysis.get('dynamic_threshold_samples')
            else:
                price_momentum = self.check_price_momentum_simple(df_slice)
                telemetry_record['positive'] = bool(price_momentum)

            self.momentum_logs.append(telemetry_record)

            # Yeni filtreler
            volume_spike = self.check_volume_spike_simple(df_slice)
            trend_strength = self.check_trend_strength_simple(df_slice)
            if volume_spike:
                self.debug_counts['filt_vol'] += 1
            if price_momentum:
                self.debug_counts['filt_mom'] += 1
            if trend_strength:
                self.debug_counts['filt_trend'] += 1
            
            filter_score = sum([volume_spike, price_momentum, trend_strength])
            
            # Giriş koşulu (4 AŞAMALI FİLTRE - BACKTEST VERSİYONU):
            # 1. Trend Filtresi: Fiyat > EMA200 VE Fiyat > EMA50 (Kesin Şart)
            # 2. Momentum/Hacim: Skor en az 2 olmalı (RSI, MACD veya Hacimden en az 2'si onay vermeli)
            # Not: Backtest'te intraday verisi olmadığı için MTF (Aşama 4) yerine günlük trend gücüne bakıyoruz.
            
            entry_ok = bool(regime and direction and (score >= 2))
            
            if entry_ok:
                self.debug_counts['entry_true'] += 1
                return {
                    'symbol': symbol,
                    'price': safe_float(last_row['Close']),
                    'atr': safe_float(last_row['atr']),
                    'entry_ok': True,
                    'date': date
                }
            return None
            
        except Exception:
            self.debug_counts['exceptions'] += 1
            return None
    
    def check_volume_spike_simple(self, df):
        """Basit hacim kontrolü"""
        try:
            if len(df) < 10:
                return False
            current_vol = safe_float(df['Volume'].iloc[-1])
            avg_vol = safe_float(df['Volume'].rolling(10).mean().iloc[-1])
            return current_vol > avg_vol * 1.2
        except Exception:
            return False
    
    def check_price_momentum_simple(self, df):
        """Basit momentum kontrolü"""
        try:
            if len(df) < 4:
                return False
            current = safe_float(df['Close'].iloc[-1])
            past = safe_float(df['Close'].iloc[-4])
            if past == 0:
                return False
            change_pct = ((current - past) / past) * 100
            return change_pct >= 1.5
        except Exception:
            return False
    
    def check_trend_strength_simple(self, df):
        """Basit trend gücü kontrolü"""
        try:
            if len(df) < 200:
                return False
            ema50 = safe_float(df['ema50'].iloc[-1])
            ema200 = safe_float(df['ema200'].iloc[-1])
            if ema200 == 0:
                return False
            strength_pct = ((ema50 - ema200) / ema200) * 100
            return strength_pct >= 3.0
        except Exception:
            return False
    
    def execute_trade(self, symbol, signal, entry_date):
        """İşlem yap (ATR ve Kelly tabanlı pozisyon sizing) - Kademeli Çıkışlı"""
        try:
            # --- Pyramiding & Cooldown Kontrolü ---
            # Aynı sembolde açık işlem varsa veya son işlemden sonra yeterince süre geçmediyse girme
            entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d")
            cooldown_days = 3 
            
            for t in self.trades:
                if t['symbol'] == symbol:
                    # Tarih formatı kontrolü (bazen saat bilgisi olabiliyor)
                    exit_str = t['exit_date'].split(' ')[0] if ' ' in t['exit_date'] else t['exit_date']
                    try:
                        exit_date_obj = datetime.strptime(exit_str, "%Y-%m-%d")
                        # Eğer yeni giriş tarihi, önceki işlemin çıkış tarihinden önceyse (çakışma/açık pozisyon)
                        if entry_date_obj <= exit_date_obj:
                            return
                        # Eğer yeni giriş tarihi, önceki çıkış + cooldown süresi içindeyse
                        if entry_date_obj <= exit_date_obj + timedelta(days=cooldown_days):
                            return
                    except ValueError:
                        continue

            entry_price = signal['price']
            atr = signal.get('atr', 0.01)
            
            # --- Kademeli Hedef ve Dinamik Stop (Normal Mod Varsayılan) ---
            # Backtest için şimdilik "Normal Mod" varsayıyoruz.
            # İleride momentum skorunu signal içine ekleyip buraya taşıyabiliriz.
            stop_loss = entry_price - (atr * 2.0)
            tp1 = entry_price + (atr * 4.0)
            tp2 = entry_price + (atr * 6.0)
            tp3 = entry_price + (atr * 9.0)

            # ATR tabanlı risk
            price_risk = entry_price - stop_loss
            if price_risk <= 0:
                return

            # Modifiye Kelly kriteri ile pozisyon büyüklüğü
            # Kelly = WinRate - (1 - WinRate) / (AvgWin / abs(AvgLoss))
            win_rate = 0.5  # Varsayılan, optimize edilebilir
            avg_win = 2.0   # Varsayılan, optimize edilebilir
            avg_loss = 1.0  # Varsayılan, optimize edilebilir
            if hasattr(self, 'trades') and len(self.trades) > 10:
                wins = [t['pnl'] for t in self.trades if t['pnl'] > 0]
                losses = [t['pnl'] for t in self.trades if t['pnl'] < 0]
                win_rate = len(wins) / len(self.trades) if self.trades else 0.5
                avg_win = sum(wins) / len(wins) if wins else 2.0
                avg_loss = abs(sum(losses) / len(losses)) if losses else 1.0
            kelly = (win_rate - (1 - win_rate) / (avg_win / avg_loss)) if avg_loss > 0 else 0.1
            kelly = max(0.01, min(kelly, 1.0))  # 0.01 ile 1.0 arası
            kelly_position = self.current_portfolio * self.kelly_fraction * kelly

            # ATR tabanlı risk ile minimumu al
            risk_amount_atr = (self.current_portfolio * self.risk_percent / 100)
            
            # Risk sermayesine göre hisse adedi
            risk_based_shares = min(kelly_position, risk_amount_atr) / price_risk
            
            # --- MANTIKSAL POZİSYON LİMİTİ (Hard Cap) ---
            # Portföyün en fazla %10'unu tek bir hisseye yatırabiliriz.
            # Bu, aşırı kaldıraç ve konsantrasyon riskini önler.
            max_allocation_pct = 0.10 
            max_position_value = self.current_portfolio * max_allocation_pct
            max_shares_by_value = max_position_value / entry_price
            
            # Nihai hisse adedi (Risk ve Bütçe kısıtlarının en küçüğü)
            position_size = min(risk_based_shares, max_shares_by_value)
            
            if position_size <= 0:
                return

            # İşlem sonucunu simüle et (Kademeli Çıkış)
            exits = self.simulate_exit(symbol, entry_date, entry_price, stop_loss, tp1, tp2, tp3)

            if exits:
                total_pnl_net = 0
                total_commission = 0
                weighted_exit_price = 0
                total_fraction = 0
                
                exit_reasons = []
                last_exit_date = entry_date

                for exit_trade in exits:
                    fraction = exit_trade['fraction']
                    exit_price = exit_trade['price']
                    exit_date = exit_trade['date']
                    reason = exit_trade['reason']
                    
                    part_size = position_size * fraction
                    
                    slip = self.slippage_bps / 10000.0
                    entry_exec = entry_price * (1 + slip)
                    exit_exec = exit_price * (1 - slip)
                    commission_rate = self.commission_bps / 10000.0
                    
                    commission = commission_rate * (entry_exec * part_size + exit_exec * part_size)
                    pnl_gross = (exit_exec - entry_exec) * part_size
                    pnl_net = pnl_gross - commission
                    
                    total_pnl_net += pnl_net
                    total_commission += commission
                    weighted_exit_price += exit_price * fraction
                    total_fraction += fraction
                    
                    exit_reasons.append(f"{reason}({int(fraction*100)}%)")
                    last_exit_date = exit_date

                avg_exit_price = weighted_exit_price / total_fraction if total_fraction > 0 else 0
                
                # R-Multiple (Toplam PnL / Başlangıç Riski)
                # Başlangıç riski = (Entry - Stop) * Position Size
                initial_risk_dollar = price_risk * position_size
                r_multiple = total_pnl_net / initial_risk_dollar if initial_risk_dollar > 0 else 0.0
                
                pnl_pct = (total_pnl_net / (entry_price * position_size)) * 100 if entry_price * position_size > 0 else 0.0

                trade = {
                    'symbol': symbol,
                    'entry_date': entry_date,
                    'entry_price': entry_price,
                    'exit_date': last_exit_date,
                    'exit_price': avg_exit_price, # Ortalama çıkış fiyatı
                    'shares': position_size,
                    'stop_loss': stop_loss,
                    'take_profit': tp2, # Ana hedefi göster
                    'pnl': total_pnl_net,
                    'pnl_pct': pnl_pct,
                    'commission': total_commission,
                    'r_multiple': r_multiple,
                    'reason': ", ".join(exit_reasons),
                    'kelly': kelly,
                    'kelly_position': kelly_position
                }
                self.trades.append(trade)
                self.current_portfolio += trade['pnl']
        except Exception:
            pass
    
    def simulate_exit(self, symbol, entry_date, entry_price, stop_loss, tp1, tp2, tp3):
        """Çıkış simülasyonu (Kademeli + Trailing Stop)"""
        try:
            # Giriş tarihinden 90 gün sonrasına kadar veri al (Runner için süre uzatıldı)
            entry_date_obj = datetime.strptime(entry_date, "%Y-%m-%d")
            end_date = entry_date_obj + timedelta(days=90)
            
            df = yf.download(symbol, start=entry_date, end=end_date.strftime("%Y-%m-%d"), progress=False)

            if df is None or not isinstance(df, pd.DataFrame):
                return None
            
            if df.empty:
                return None
            
            exits = []
            remaining_fraction = 1.0
            
            # Initialize with last available data in case loop doesn't set them
            last_row = df.iloc[-1]
            close = float(last_row['Close'])
            date_str = str(df.index[-1])
            if ' ' in date_str:
                date_str = date_str.split(' ')[0]
            elif 'T' in date_str:
                date_str = date_str.split('T')[0]
            elif len(date_str) >= 10:
                date_str = date_str[:10]

            # Trailing Stop için değişkenler
            highest_price = entry_price
            # TP3 yerine Trailing Stop kullanacağız.
            # Trailing mesafesi: TP2'ye ulaştıktan sonra ATR'nin 2.5 katı kadar geriden gelsin
            # Veya basitçe: Fiyat yükseldikçe stop'u yukarı çek
            # Burada "ATR" değerine ihtiyacımız var. Parametre olarak gelmediği için
            # stop_loss mesafesinden ATR'yi tahmin edebiliriz: ATR ~ (entry - stop_loss) / 2.0
            estimated_atr = (entry_price - stop_loss) / 2.0
            trailing_dist = estimated_atr * 2.5
            
            # Dinamik stop (başlangıçta sabit stop_loss)
            current_stop = stop_loss

            # Her gün kontrol et
            for i, (idx, row) in enumerate(df.iterrows()):
                if i == 0:  # Giriş günü atla
                    continue
                    
                high = float(row['High'])
                low = float(row['Low'])
                close = float(row['Close'])
                
                # En yüksek fiyatı güncelle (Trailing için)
                if high > highest_price:
                    highest_price = high
                
                # Trailing Stop Güncellemesi (Sadece TP2 alındıktan sonra veya her zaman?)
                # Strateji: TP2 alındıktan sonra kalan %20 için trailing stop devreye girer.
                # Ancak TP1 alındıktan sonra stop'u girişe çekmek de iyi bir pratiktir (Breakeven).
                
                date_str = str(idx)
                if ' ' in date_str:
                    date_str = date_str.split(' ')[0]
                elif 'T' in date_str:
                    date_str = date_str.split('T')[0]
                elif len(date_str) >= 10:
                    date_str = date_str[:10]
                
                # 1. Stop Loss Kontrolü (Mevcut stop seviyesine göre)
                if low <= current_stop:
                    exits.append({
                        'date': date_str,
                        'price': current_stop,
                        'fraction': remaining_fraction,
                        'reason': 'trailing_stop' if current_stop > stop_loss else 'stop_loss'
                    })
                    return exits
                
                # 2. TP1 Kontrolü (%50)
                if remaining_fraction >= 1.0 and high >= tp1:
                    exits.append({
                        'date': date_str,
                        'price': tp1,
                        'fraction': 0.5,
                        'reason': 'tp1'
                    })
                    remaining_fraction -= 0.5
                    # TP1 alındı, Stop'u Giriş Seviyesine (Breakeven) çek
                    current_stop = max(current_stop, entry_price)
                    
                # 3. TP2 Kontrolü (%30)
                if remaining_fraction >= 0.5 and high >= tp2:
                    exits.append({
                        'date': date_str,
                        'price': tp2,
                        'fraction': 0.3,
                        'reason': 'tp2'
                    })
                    remaining_fraction -= 0.3
                    # TP2 alındı, Trailing Stop Aktif!
                    # Stop seviyesini (Zirve - 2.5 ATR) seviyesine çek
                    new_stop = highest_price - trailing_dist
                    current_stop = max(current_stop, new_stop)
                    
                # 4. TP3 / Runner Kontrolü (%20)
                # Artık sabit TP3 yok, sadece Trailing Stop var.
                # Ancak kalan %20 için stop seviyesini her gün güncellememiz lazım.
                if remaining_fraction <= 0.25: # TP2 alındıysa (yaklaşık 0.2 kaldı)
                    new_stop = highest_price - trailing_dist
                    current_stop = max(current_stop, new_stop)

            # Süre doldu, kalanları kapat
            if remaining_fraction > 0:
                exits.append({
                    'date': date_str,
                    'price': close,
                    'fraction': remaining_fraction,
                    'reason': 'timeout'
                })
                
            return exits

        except Exception:
            return None
    
    def calculate_results(self):
        """Sonuçları hesapla ve göster"""
        # Her durumda sinyal sayısını göster
        try:
            print(f"\n🧭 Tespit edilen giriş sinyali sayısı: {self.signals_found}")
        except Exception:
            pass
        if not self.trades:
            if hasattr(self, 'debug_counts'):
                dc = self.debug_counts
                print("\n🛠️ Tanılama:")
                print(f"   • simulate_calls: {dc.get('simulate_calls',0)}")
                print(f"   • df_missing: {dc.get('df_missing',0)} | slice_short: {dc.get('slice_short',0)} | exceptions: {dc.get('exceptions',0)}")
                print(f"   • score_rsi: {dc.get('score_rsi',0)} | score_vol: {dc.get('score_vol',0)} | score_macd: {dc.get('score_macd',0)}")
                print(f"   • filt_vol: {dc.get('filt_vol',0)} | filt_mom: {dc.get('filt_mom',0)} | filt_trend: {dc.get('filt_trend',0)}")
                print(f"   • entry_true: {dc.get('entry_true',0)}")
            if getattr(self, 'signals_found', 0) > 0:
                print("⚠️ Sinyal tespit edildi ancak işlem açılamadı (ATR/hacim/hesaplama).")
            print("❌ Hiç işlem bulunamadı!")
            return
        
        print("\n🎯 BACKTEST SONUÇLARI")
        print("=" * 40)
        if hasattr(self, 'debug_counts'):
            dc = self.debug_counts
            print("\n🛠️ Tanılama:")
            print(f"   • simulate_calls: {dc.get('simulate_calls',0)}")
            print(f"   • df_missing: {dc.get('df_missing',0)} | slice_short: {dc.get('slice_short',0)} | exceptions: {dc.get('exceptions',0)}")
            print(f"   • score_rsi: {dc.get('score_rsi',0)} | score_vol: {dc.get('score_vol',0)} | score_macd: {dc.get('score_macd',0)}")
            print(f"   • filt_vol: {dc.get('filt_vol',0)} | filt_mom: {dc.get('filt_mom',0)} | filt_trend: {dc.get('filt_trend',0)}")
            print(f"   • entry_true: {dc.get('entry_true',0)}")
        
        # Temel istatistikler
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        total_return = self.current_portfolio - self.start_portfolio
        total_return_pct = (total_return / self.start_portfolio) * 100
        
        avg_win = sum([t['pnl'] for t in self.trades if t['pnl'] > 0]) / winning_trades if winning_trades > 0 else 0
        avg_loss = sum([t['pnl'] for t in self.trades if t['pnl'] < 0]) / losing_trades if losing_trades > 0 else 0
        
        print(f"💰 Başlangıç: ${self.start_portfolio:,.2f}")
        print(f"💰 Bitiş: ${self.current_portfolio:,.2f}")
        print(f"📈 Toplam Getiri: ${total_return:,.2f} ({total_return_pct:.2f}%)")
        print("\n📊 İşlem İstatistikleri:")
        print(f"   • Toplam İşlem: {total_trades}")
        print(f"   • Kazanan: {winning_trades} ({win_rate:.1f}%)")
        print(f"   • Kaybeden: {losing_trades} ({100-win_rate:.1f}%)")
        print(f"   • Ortalama Kazanç: ${avg_win:.2f}")
        print(f"   • Ortalama Kayıp: ${avg_loss:.2f}")
        # Sinyal sayısını tekrar göster (özet tablosu öncesi)
        try:
            print(f"\n🧭 Tespit edilen giriş sinyali sayısı: {self.signals_found}")
        except Exception:
            pass
        
        if avg_loss != 0:
            profit_factor = abs(avg_win / avg_loss)
            print(f"   • Profit Factor: {profit_factor:.2f}")

        # Yeni: Maliyet/Slippage etkisi ve R beklentisi
        avg_commission = sum([t.get('commission', 0) for t in self.trades]) / total_trades if total_trades > 0 else 0
        avg_r = sum([t.get('r_multiple', 0.0) for t in self.trades]) / total_trades if total_trades > 0 else 0.0
        expectancy = avg_r  # işlem başına beklenen R
        print(f"   • Ortalama Komisyon: ${avg_commission:.2f} (işlem başına)")
        print(f"   • Ortalama R: {avg_r:.2f}")
        print(f"   • Expectancy (R): {expectancy:.2f}")

        # Yeni: CAGR, Sharpe, Max DD (günlük seri üzerinden)
        try:
            df_eq = pd.DataFrame(self.daily_portfolio)
            df_eq['date'] = pd.to_datetime(df_eq['date'])
            df_eq = df_eq.sort_values('date')
            if len(df_eq) >= 2:
                days = (df_eq['date'].iloc[-1] - df_eq['date'].iloc[0]).days or 1
                start_val = float(df_eq['portfolio_value'].iloc[0])
                end_val = float(df_eq['portfolio_value'].iloc[-1])
                cagr = ((end_val / start_val) ** (365.0 / days) - 1.0) if start_val > 0 else 0.0

                # Günlük getiri ve Sharpe
                returns = df_eq['portfolio_value'].pct_change().fillna(0.0)
                mean_r = returns.mean()
                std_r = returns.std(ddof=0)
                sharpe = (mean_r / std_r * (252 ** 0.5)) if std_r > 0 else 0.0

                # Maksimum drawdown
                running_max = df_eq['portfolio_value'].cummax()
                drawdown = (df_eq['portfolio_value'] / running_max) - 1.0
                max_dd = drawdown.min()

                print("\n📈 Risk Ayarlı Metrikler:")
                print(f"   • CAGR: {cagr*100:.2f}%")
                print(f"   • Sharpe (günlük→yıllık): {sharpe:.2f}")
                print(f"   • Max Drawdown: {max_dd*100:.2f}%")
        except Exception:
            pass

        if self.momentum_logs:
            try:
                df_mom = pd.DataFrame(self.momentum_logs)
                total_mom = len(df_mom)
                positive_mom = int(df_mom['positive'].sum()) if 'positive' in df_mom else 0
                ratio = (positive_mom / total_mom * 100) if total_mom else 0
                print("\n📐 Momentum Telemetrisi:")
                print(f"   • Pozitif momentum sinyali: {positive_mom}/{total_mom} ({ratio:.1f}%)")

                if 'threshold_effective' in df_mom:
                    thresh_eff = pd.to_numeric(df_mom['threshold_effective'], errors='coerce')
                    if thresh_eff.notna().any():
                        print(f"   • Ortalama etkin eşik: ±{thresh_eff.dropna().mean():.2f}σ")

                if 'threshold_base' in df_mom:
                    thresh_base = pd.to_numeric(df_mom['threshold_base'], errors='coerce')
                    if thresh_base.notna().any():
                        print(f"   • Ortalama baz eşik: ±{thresh_base.dropna().mean():.2f}σ")

                if 'threshold_dynamic' in df_mom:
                    thresh_dyn = pd.to_numeric(df_mom['threshold_dynamic'], errors='coerce')
                    if thresh_dyn.notna().any():
                        print(f"   • Ortalama dinamik eşik: ±{thresh_dyn.dropna().mean():.2f}σ")

                if 'liquidity_segment' in df_mom:
                    seg_counts = df_mom['liquidity_segment'].dropna().value_counts()
                    if not seg_counts.empty:
                        print("   • Segment dağılımı:")
                        for seg, count in seg_counts.items():
                            pct = count / total_mom * 100
                            print(f"      - {seg}: {count} (%{pct:.1f})")

                if 'dynamic_samples' in df_mom:
                    samples = pd.to_numeric(df_mom['dynamic_samples'], errors='coerce').dropna()
                    if not samples.empty:
                        print(f"   • Dinamik örnek medyanı: {samples.median():.0f}")
            except Exception:
                pass
        
        # 🔍 YENİ: DETAYLI ANALİZ
        print("\n🔍 DETAYLI ANALİZ:")
        self.analyze_trade_frequency()
        self.analyze_trade_timing() 
        self.show_trade_examples()
        self.analyze_win_loss_patterns()
        
        # En iyi ve en kötü işlemler
        if self.trades:
            best_trade = max(self.trades, key=lambda x: x['pnl'])
            worst_trade = min(self.trades, key=lambda x: x['pnl'])
            
            print(f"\n🏆 En İyi İşlem: {best_trade['symbol']} (${best_trade['pnl']:.2f})")
            print(f"💀 En Kötü İşlem: {worst_trade['symbol']} (${worst_trade['pnl']:.2f})")
        
        # Sonuç değerlendirmesi
        print("\n🎯 SONUÇ:")
        if win_rate >= 60 and total_return_pct >= 15:
            print("🟢 MÜKEMMEL! Sistem çok başarılı!")
        elif win_rate >= 50 and total_return_pct >= 10:
            print("🟡 İYİ! Sistem karlı ve güvenilir!")
        elif win_rate >= 40 and total_return_pct >= 5:
            print("🟠 ORTA! Sistem geliştirilmeli!")
        else:
            print("🔴 KÖTÜ! Sistem revize edilmeli!")

    def analyze_trade_frequency(self):
        """İşlem sıklığı analizi"""
        if not self.trades:
            return
            
        # Günlük işlem sayısı
        trade_dates = [t['entry_date'] for t in self.trades]
        unique_dates = set(trade_dates)
        
        trades_per_day = len(self.trades) / len(unique_dates) if unique_dates else 0
        
        print(f"   📅 İşlem Günleri: {len(unique_dates)}")
        print(f"   📊 Günlük Ortalama İşlem: {trades_per_day:.1f}")
        
        # En aktif günler
        from collections import Counter
        date_counts = Counter(trade_dates)
        most_active = date_counts.most_common(3)
        
        print("   🔥 En Aktif Günler:")
        for date, count in most_active:
            print(f"      • {date}: {count} işlem")

    def analyze_trade_timing(self):
        """İşlem zamanlaması analizi""" 
        if not self.trades:
            return
            
        # İşlem süreleri
        from datetime import datetime
        durations = []
        
        for trade in self.trades:
            try:
                entry_date = datetime.strptime(trade['entry_date'], '%Y-%m-%d')
                exit_date = datetime.strptime(trade['exit_date'], '%Y-%m-%d')
                duration = (exit_date - entry_date).days
                durations.append(duration)
            except Exception:
                continue
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            
            print(f"   ⏱️ Ortalama İşlem Süresi: {avg_duration:.1f} gün")
            print(f"   ⚡ En Kısa İşlem: {min_duration} gün")
            print(f"   🐌 En Uzun İşlem: {max_duration} gün")
        
        # Çıkış nedenleri
        exit_reasons = [t['reason'] for t in self.trades]
        from collections import Counter
        reason_counts = Counter(exit_reasons)
        
        print("   🚪 Çıkış Nedenleri:")
        for reason, count in reason_counts.items():
            percentage = (count / len(self.trades)) * 100
            reason_name = {
                'stop_loss': 'Stop-Loss',
                'take_profit': 'Take-Profit', 
                'time_exit': 'Zaman Doldu'
            }.get(reason, reason)
            print(f"      • {reason_name}: {count} ({percentage:.1f}%)")

    def show_trade_examples(self):
        """Örnek işlemler göster"""
        if not self.trades or len(self.trades) < 5:
            return
        
        print("\n📝 ÖRNEK İŞLEMLER (İlk 5):")
        print("-" * 80)
        
        for i, trade in enumerate(self.trades[:5], 1):
            status = "✅ KAZANÇ" if trade['pnl'] > 0 else "❌ KAYIP"
            duration = "?"
            
            try:
                entry_date = datetime.strptime(trade['entry_date'], '%Y-%m-%d')
                exit_date = datetime.strptime(trade['exit_date'], '%Y-%m-%d')
                duration = f"{(exit_date - entry_date).days} gün"
            except Exception:
                pass
                
            reason_name = {
                'stop_loss': 'Stop-Loss',
                'take_profit': 'Take-Profit', 
                'time_exit': 'Zaman Doldu'
            }.get(trade['reason'], trade['reason'])
            
            print(f"{i}. {trade['symbol']} - {status}")
            print(f"   📅 {trade['entry_date']} → {trade['exit_date']} ({duration})")
            print(f"   💰 ${trade['entry_price']:.2f} → ${trade['exit_price']:.2f}")
            print(f"   📊 P&L: ${trade['pnl']:.2f} ({trade['pnl_pct']:.2f}%)")
            print(f"   🚪 Çıkış: {reason_name}")
            print()

    def analyze_win_loss_patterns(self):
        """Kazanç/kayıp paternlerini analiz et"""
        if not self.trades:
            return
            
        # Sembol bazlı performans
        symbol_performance = {}
        for trade in self.trades:
            symbol = trade['symbol']
            if symbol not in symbol_performance:
                symbol_performance[symbol] = {'wins': 0, 'losses': 0, 'total_pnl': 0}
            
            if trade['pnl'] > 0:
                symbol_performance[symbol]['wins'] += 1
            else:
                symbol_performance[symbol]['losses'] += 1
            symbol_performance[symbol]['total_pnl'] += trade['pnl']
        
        # En başarılı semboller
        successful_symbols = []
        for symbol, perf in symbol_performance.items():
            total_trades = perf['wins'] + perf['losses']
            win_rate = (perf['wins'] / total_trades) * 100 if total_trades > 0 else 0
            if total_trades >= 5:  # En az 5 işlem
                successful_symbols.append((symbol, win_rate, perf['total_pnl'], total_trades))
        
        successful_symbols.sort(key=lambda x: x[1], reverse=True)  # Win rate'e göre sırala
        
        if successful_symbols:
            print("\n🏆 EN BAŞARILI SEMBOLLER (Min 5 İşlem):")
            for symbol, win_rate, total_pnl, total_trades in successful_symbols[:5]:
                print(f"   • {symbol}: %{win_rate:.1f} başarı ({total_trades} işlem, ${total_pnl:.2f})")
        
        # Başarı oranı düşüş analizi
        print("\n📉 BAŞARI ORANI ANALİZİ:")
        winning_trades = len([t for t in self.trades if t['pnl'] > 0])
        current_win_rate = (winning_trades / len(self.trades)) * 100
        
        print(f"   • Mevcut Başarı Oranı: %{current_win_rate:.1f}")
        print("   • Hedef Başarı Oranı: %73+")
        
        if current_win_rate < 65:
            print("   ⚠️ UYARI: Başarı oranı hedefin altında!")
            print("   💡 Çözüm Önerileri:")
            print("      - Filtreleri sıkılaştır")
            print("      - Stop-loss stratejisini gözden geçir") 
            print("      - Zaman çıkışını kısalt (30 gün → 20 gün)")
            print("      - Momentum filtrelerini güçlendir")


def main():
    """Ana backtest fonksiyonu"""
    args = parse_args()
    settings = configure_scanner_settings(args)

    print("🧪 SADE BACKTEST BAŞLIYOR")
    print("=" * 30)

    end_date = datetime.now()
    if args.end:
        try:
            end_date = datetime.strptime(args.end, "%Y-%m-%d")
        except ValueError:
            raise SystemExit("--end tarihi YYYY-MM-DD formatında olmalıdır")

    if args.start:
        try:
            start_date = datetime.strptime(args.start, "%Y-%m-%d")
        except ValueError:
            raise SystemExit("--start tarihi YYYY-MM-DD formatında olmalıdır")
    else:
        start_date = end_date - timedelta(days=int(args.window_days))

    if start_date > end_date:
        raise SystemExit("Başlangıç tarihi, bitiş tarihinden sonra olamaz.")

    symbols = resolve_symbols(args)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    print(f"📅 Tarih aralığı: {start_str} → {end_str}")
    print(f"📦 Sembol sayısı: {len(symbols)}")
    print("⚙️ Momentum ayarları:")
    dynamic_state = "Açık" if settings.get("momentum_dynamic_enabled") else "Kapalı"
    print(f"   • Dinamik z-eşiği: {dynamic_state} (pencere {settings.get('momentum_dynamic_window')} gün, yüzdelik {settings.get('momentum_dynamic_quantile')})")
    print(f"   • Lookback (σ): {settings.get('momentum_baseline_window')} gün")
    presets_state = "Açık" if settings.get("momentum_segment_thresholds") else "Kapalı"
    print(f"   • Likidite preset'leri: {presets_state}")

    bt = SimpleBacktest(
        start_portfolio=float(args.portfolio),
        risk_per_trade=float(args.risk),
        kelly_fraction=float(args.kelly)
    )
    bt.backtest_period(symbols=symbols, start_date=start_str, end_date=end_str)

if __name__ == "__main__":
    main()
