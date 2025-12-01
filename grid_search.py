# grid_search.py
"""
Basit grid search fonksiyonu: RSI üst bandı, hacim çarpanı, momentum yüzdesi gibi parametreleri sistematik olarak dener ve sonuçları kaydeder.
"""
import itertools
from backtest import SimpleBacktest
from scanner import load_symbols
import pandas as pd


# --- Walk-Forward Optimizasyon (WFO) Fonksiyonu ---
def run_wfo_grid_search(
    rsi_upper_list=[55, 60, 65, 70],
    volume_mult_list=[1.0, 1.1, 1.2, 1.3],
    momentum_pct_list=[0.5, 1.0, 1.5, 2.0],
    start_date="2023-01-01",
    end_date="2023-12-31",
    train_window_days=120,
    test_window_days=30
):
    symbols = load_symbols()
    results = []
    # Tarih aralığını rolling window ile böl
    date_range = pd.date_range(start=start_date, end=end_date)
    i = 0
    while i + train_window_days + test_window_days <= len(date_range):
        train_start = date_range[i]
        train_end = date_range[i + train_window_days - 1]
        test_start = date_range[i + train_window_days]
        test_end = date_range[i + train_window_days + test_window_days - 1]
        print(f"\n--- WFO Adımı: Eğitim {train_start.date()} → {train_end.date()} | Test {test_start.date()} → {test_end.date()} ---")
        # 1. Grid search ile en iyi parametreleri bul (train window)
        best_params = None
        best_score = -float('inf')
        for rsi_upper, vol_mult, mom_pct in itertools.product(rsi_upper_list, volume_mult_list, momentum_pct_list):
            import scanner
            scanner.SETTINGS['rsi_upper'] = rsi_upper
            scanner.SETTINGS['volume_mult'] = vol_mult
            scanner.SETTINGS['momentum_pct'] = mom_pct
            bt = SimpleBacktest()
            bt.backtest_period(symbols, train_start.strftime("%Y-%m-%d"), train_end.strftime("%Y-%m-%d"))
            res = bt.calculate_results()
            if res is None:
                res = {'CAGR': None, 'Sharpe': None, 'MaxDD': None, 'WinRate': None, 'AvgR': None, 'Expectancy': None}
            score = res.get('CAGR', 0) or 0
            if score > best_score:
                best_score = score
                best_params = {
                    'rsi_upper': rsi_upper,
                    'volume_mult': vol_mult,
                    'momentum_pct': mom_pct
                }
        # 2. En iyi parametrelerle out-of-sample test (test window)
        if best_params is not None:
            import scanner
            scanner.SETTINGS['rsi_upper'] = best_params['rsi_upper']
            scanner.SETTINGS['volume_mult'] = best_params['volume_mult']
            scanner.SETTINGS['momentum_pct'] = best_params['momentum_pct']
            bt_test = SimpleBacktest()
            bt_test.backtest_period(symbols, test_start.strftime("%Y-%m-%d"), test_end.strftime("%Y-%m-%d"))
            res_test = bt_test.calculate_results()
            if res_test is None:
                res_test = {'CAGR': None, 'Sharpe': None, 'MaxDD': None, 'WinRate': None, 'AvgR': None, 'Expectancy': None}
            results.append({
                'train_start': train_start.date(),
                'train_end': train_end.date(),
                'test_start': test_start.date(),
                'test_end': test_end.date(),
                'rsi_upper': best_params['rsi_upper'],
                'volume_mult': best_params['volume_mult'],
                'momentum_pct': best_params['momentum_pct'],
                'CAGR': res_test.get('CAGR'),
                'Sharpe': res_test.get('Sharpe'),
                'MaxDD': res_test.get('MaxDD'),
                'WinRate': res_test.get('WinRate'),
                'AvgR': res_test.get('AvgR'),
                'Expectancy': res_test.get('Expectancy')
            })
        else:
            # Hiç parametre bulunamazsa boş satır ekle
            results.append({
                'train_start': train_start.date(),
                'train_end': train_end.date(),
                'test_start': test_start.date(),
                'test_end': test_end.date(),
                'rsi_upper': None,
                'volume_mult': None,
                'momentum_pct': None,
                'CAGR': None,
                'Sharpe': None,
                'MaxDD': None,
                'WinRate': None,
                'AvgR': None,
                'Expectancy': None
            })
        i += test_window_days
    df_results = pd.DataFrame(results)
    df_results.to_csv('wfo_grid_search_results.csv', index=False)
    print("WFO grid search tamamlandı. Sonuçlar wfo_grid_search_results.csv dosyasına kaydedildi.")
    print(df_results.head(10))
    return df_results

# Eski grid search fonksiyonu korunabilir

def run_grid_search(
    rsi_upper_list=[55, 60, 65, 70],
    volume_mult_list=[1.0, 1.1, 1.2, 1.3],
    momentum_pct_list=[0.5, 1.0, 1.5, 2.0],
    start_date="2023-01-01",
    end_date="2023-12-31"
):
    symbols = load_symbols()
    results = []
    for rsi_upper, vol_mult, mom_pct in itertools.product(rsi_upper_list, volume_mult_list, momentum_pct_list):
        print(f"Test: RSI<={rsi_upper}, Hacim>{vol_mult}x, Momentum>={mom_pct}%")
        import scanner
        scanner.SETTINGS['rsi_upper'] = rsi_upper
        scanner.SETTINGS['volume_mult'] = vol_mult
        scanner.SETTINGS['momentum_pct'] = mom_pct
        bt = SimpleBacktest()
        bt.backtest_period(symbols, start_date, end_date)
        res = bt.calculate_results()
        if res is None:
            res = {'CAGR': None, 'Sharpe': None, 'MaxDD': None, 'WinRate': None, 'AvgR': None, 'Expectancy': None}
        results.append({
            'rsi_upper': rsi_upper,
            'volume_mult': vol_mult,
            'momentum_pct': mom_pct,
            'CAGR': res.get('CAGR'),
            'Sharpe': res.get('Sharpe'),
            'MaxDD': res.get('MaxDD'),
            'WinRate': res.get('WinRate'),
            'AvgR': res.get('AvgR'),
            'Expectancy': res.get('Expectancy')
        })
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values(by=['CAGR', 'Sharpe', 'WinRate'], ascending=[False, False, False])
    df_results.to_csv('grid_search_results.csv', index=False)
    print("Grid search tamamlandı. Sonuçlar grid_search_results.csv dosyasına kaydedildi.")
    print(df_results.head(10))
    return df_results

if __name__ == "__main__":
    run_wfo_grid_search()
