import argparse
import os
import sys
from datetime import datetime
import pandas as pd

import scanner


def parse_args():
    p = argparse.ArgumentParser(description="Scan a CSV of symbols and select suitable ones")
    p.add_argument("--input", required=True, help="Path to CSV file containing a 'Symbol' or 'Ticker' column")
    p.add_argument("--aggressive", action="store_true", help="Use aggressive thresholds")
    return p.parse_args()


def extract_symbols(csv_path: str):
    df = pd.read_csv(csv_path)
    for col in ["Symbol", "Ticker", "symbol", "ticker"]:
        if col in df.columns:
            syms = [str(s).strip().upper() for s in df[col].dropna().tolist()]
            return [s for s in syms if s and s != "nan"]
    raise ValueError("CSV must contain a 'Symbol' or 'Ticker' column")


def main():
    args = parse_args()

    # Apply settings mode
    if args.aggressive:
        s = scanner.DEFAULT_SETTINGS.copy()
        s.update(scanner.AGGRESSIVE_OVERRIDES)
        scanner.SETTINGS = s
    else:
        scanner.SETTINGS = scanner.DEFAULT_SETTINGS.copy()

    csv_path = os.path.abspath(args.input)
    if not os.path.exists(csv_path):
        print(f"CSV bulunamadı: {csv_path}")
        sys.exit(1)

    symbols = extract_symbols(csv_path)
    if not symbols:
        print("CSV'de işlenecek sembol yok.")
        sys.exit(1)

    print(f"🔎 CSV'den {len(symbols)} sembol bulundu. Tarama başlıyor…")
    results = scanner.evaluate_symbols_parallel(symbols)
    if not results:
        print("Sonuç yok. Veri/bağlantı kontrol edin.")
        sys.exit(0)

    import pandas as _pd
    df = _pd.DataFrame(results)
    df = df.sort_values(["entry_ok", "score"], ascending=[False, False])

    ts = datetime.now().strftime("%Y%m%d_%H%M")
    base = os.path.splitext(os.path.basename(csv_path))[0]
    out_short = f"shortlist_fromcsv_{base}_{ts}.csv"
    out_sug = f"suggestions_fromcsv_{base}_{ts}.csv"
    df.to_csv(out_short, index=False)

    buyable = df[df["entry_ok"]]
    print("\n--- Alınabilecekler (entry_ok=True) ---")
    if len(buyable) > 0:
        print(buyable[["symbol", "price", "risk_reward", "timestamp"]].to_string(index=False))
    else:
        print("Uygun alım fırsatı yok.")
    print(f"\nCSV kaydedildi: {out_short}")

    # Recommendations Top 10
    try:
        df_rec = df.copy()
        df_rec["recommendation_score"] = df_rec.apply(scanner.compute_recommendation_score, axis=1)
        df_rec["strength"] = df_rec["recommendation_score"].map(scanner.compute_recommendation_strength)
        df_rec = df_rec.sort_values(["entry_ok", "recommendation_score"], ascending=[False, False])
        top10 = df_rec.head(10).copy()
        top10["why"] = top10.apply(lambda r: scanner.build_explanation(r.to_dict()), axis=1)
        top10["reason"] = top10.apply(lambda r: scanner.build_reason(r.to_dict()), axis=1)
        top10.to_csv(out_sug, index=False)
        print(f"Öneriler CSV kaydedildi: {out_sug}")
        print("\n--- Öneriler (Top 10) ---")
        for i, rec in enumerate(top10.to_dict(orient="records"), 1):
            strength = int(rec.get('strength', 0))
            print(f"{i}. {rec.get('symbol')} | Skor: {rec.get('recommendation_score'):.2f} ({strength}/100) | Entry: {'Evet' if rec.get('entry_ok') else 'Hayır'}")
            print(f"   -> {rec.get('why')}")
            print(f"   -> {rec.get('reason')}")

        # Telegram gönderimleri
        telegram = None
        try:
            from telegram_alerts import TelegramNotifier
            from telegram_config import BOT_TOKEN, CHAT_ID
            telegram = TelegramNotifier(BOT_TOKEN, CHAT_ID)
            if not telegram.is_configured():
                telegram = None
        except Exception as _e:
            telegram = None

        if telegram:
            try:
                # Top 10 öneriler – tek mesaj
                telegram.send_recommendations(top10)
            except Exception as _te:
                print(f"⚠️ Öneriler Telegram'a gönderilemedi: {_te}")

            try:
                # Günlük özet
                best_signal = buyable.iloc[0].to_dict() if len(buyable) > 0 else None
                telegram.send_daily_summary(len(buyable), best_signal)
            except Exception as _ts:
                print(f"⚠️ Özet Telegram'a gönderilemedi: {_ts}")

            try:
                # Çoklamayı önlemek için en fazla 3 sinyali tekil mesaj gönder
                for info in buyable.head(3).to_dict(orient='records'):
                    telegram.send_signal_alert(info)
            except Exception as _ti:
                print(f"⚠️ Sinyal(ler) Telegram'a gönderilemedi: {_ti}")
    except Exception as e:
        print(f"⚠️ Öneri oluşturulamadı: {e}")


if __name__ == "__main__":
    main()
