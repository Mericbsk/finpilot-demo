"""
Telegram Bot Runner - Tek tıkla tarama (/scan)
- Telefonunuzdan botunuza /scan yazın veya komut menüsünden seçin
- Bu script taramayı çalıştırır, sonuç özetini ve CSV dosyasını geri yollar
"""

import glob
import os
import subprocess
import sys
import time

import pandas as pd
import requests
from telegram_config import BOT_TOKEN, CHAT_ID

API_BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg_send_message(text: str):
    try:
        resp = requests.post(
            f"{API_BASE}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=15,
        )
        return resp.ok
    except Exception:
        return False


def tg_send_document(file_path: str, caption: str = ""):
    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{API_BASE}/sendDocument",
                data={"chat_id": CHAT_ID, "caption": caption},
                files={"document": f},
                timeout=60,
            )
        return resp.ok
    except Exception:
        return False


def latest_shortlist_csv(cwd: str) -> str | None:
    files = sorted(
        glob.glob(os.path.join(cwd, "shortlist_*.csv")), key=os.path.getmtime, reverse=True
    )
    return files[0] if files else None


def latest_suggestions_csv(cwd: str) -> str | None:
    files = sorted(
        glob.glob(os.path.join(cwd, "suggestions_*.csv")), key=os.path.getmtime, reverse=True
    )
    return files[0] if files else None


def summarize_csv(csv_path: str) -> str:
    try:
        df = pd.read_csv(csv_path)
        total = len(df)
        buyable = df[df["entry_ok"]] if "entry_ok" in df.columns else pd.DataFrame()
        buy_n = len(buyable)
        best = None
        if buy_n > 0:
            # En yüksek skor ve R/R'a göre sırala (mevcut kolonlara göre)
            sort_cols = [c for c in ["score", "risk_reward"] if c in buyable.columns]
            if sort_cols:
                best_row = buyable.sort_values(sort_cols, ascending=[False] * len(sort_cols)).iloc[
                    0
                ]
            else:
                best_row = buyable.iloc[0]
            best = best_row.to_dict()
        lines = [
            f"📊 Sonuç: {total} sembol tarandı",
            f"🎯 Alım sinyali: {buy_n} adet",
        ]
        if best:
            try:
                rr = float(best.get("risk_reward", 0) or 0)
            except Exception:
                rr = 0.0
            lines.append(
                f"🏆 En iyi: {best.get('symbol', '')} | Fiyat: ${best.get('price', '')} | R/R: {rr:.1f}"
            )
        return "\n".join(lines)
    except Exception:
        return "📊 Sonuç özeti oluşturulamadı."


def summarize_suggestions(csv_path: str, limit: int = 10) -> str:
    try:
        df = pd.read_csv(csv_path)
        if "recommendation_score" in df.columns:
            df = df.sort_values(["entry_ok", "recommendation_score"], ascending=[False, False])
        top = df.head(limit)
        lines = ["🔝 Öneriler (Top 10):"]
        for i, r in enumerate(top.to_dict(orient="records"), 1):
            lines.append(
                f"{i}. {r.get('symbol')} | Skor: {r.get('recommendation_score', '')} | Entry: {'Evet' if r.get('entry_ok') else 'Hayır'}\n   -> {r.get('why', '') or ''}"
            )
        return "\n".join(lines)
    except Exception:
        return "Öneri özeti oluşturulamadı."


def run_scan_and_report(aggressive: bool = False):
    cwd = os.path.dirname(os.path.abspath(__file__))
    tg_send_message("🔎 Tarama başlatıldı. Lütfen bekleyin…" + (" (Agresif)" if aggressive else ""))
    start = time.time()

    # scanner.py çalıştır
    try:
        cmd = [sys.executable, "scanner.py"]
        if aggressive:
            cmd.append("--aggressive")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=900,
            env=env,
            shell=False,  # Security: explicit shell=False to prevent command injection
        )
        success = proc.returncode == 0
    except subprocess.TimeoutExpired:
        tg_send_message("⏱️ Tarama zaman aşımına uğradı.")
        return
    except Exception as e:
        tg_send_message(f"❌ Tarama hata verdi: {e}")
        return

    elapsed = time.time() - start
    csv_path = latest_shortlist_csv(cwd)
    sug_path = latest_suggestions_csv(cwd)

    if not success:
        tg_send_message(f"❌ Tarama başarısız oldu. (kod {proc.returncode})")
        tail_out = (proc.stdout or "").strip()
        tail_err = (proc.stderr or "").strip()
        if tail_out:
            tg_send_message(f"stdout son bölüm:\n{tail_out[-1500:]}")
        if tail_err:
            tg_send_message(f"stderr son bölüm:\n{tail_err[-1500:]}")
        return

    # Özet mesaj
    if csv_path and os.path.exists(csv_path):
        summary = summarize_csv(csv_path)
        tg_send_message(
            f"✅ Tarama tamamlandı ({elapsed:.1f}s){' · Agresif' if aggressive else ''}\n\n{summary}"
        )
        # CSV gönder
        tg_send_document(csv_path, caption=os.path.basename(csv_path))
    else:
        tg_send_message(f"✅ Tarama tamamlandı ({elapsed:.1f}s)\n\nCSV dosyası bulunamadı.")

    # Öneriler mesajı ve CSV
    if sug_path and os.path.exists(sug_path):
        sug_summary = summarize_suggestions(sug_path, limit=10)
        tg_send_message(sug_summary)
        tg_send_document(sug_path, caption=os.path.basename(sug_path))


def poll_updates():
    tg_send_message("🤖 Bot hazır. /scan ile tarama başlatabilirsiniz.")
    offset = None
    while True:
        try:
            resp = requests.get(
                f"{API_BASE}/getUpdates", params={"timeout": 50, "offset": offset}, timeout=60
            )
            if not resp.ok:
                time.sleep(2)
                continue
            data = resp.json()
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message") or upd.get("edited_message")
                if not msg:
                    continue
                chat_id = str(msg.get("chat", {}).get("id"))
                text = (msg.get("text") or "").strip()

                # Yetkilendirme
                if chat_id != str(CHAT_ID):
                    tg_send_message("⛔ Yetkisiz kullanıcı.")
                    continue

                # Komutlar
                if text.lower() in ("/start", "start"):
                    tg_send_message("👋 Merhaba! /scan yazarak taramayı başlatabilirsiniz.")
                elif text.lower().startswith("/scan"):
                    tokens = text.lower().split()
                    is_aggr = any(
                        t in ("aggressive", "--aggressive", "aggr", "a") for t in tokens[1:]
                    )
                    run_scan_and_report(aggressive=is_aggr)
                elif text.lower().startswith("/help"):
                    tg_send_message(
                        "Kullanılabilir komutlar:\n/scan – Taramayı başlat\n/scan aggressive – Agresif mod\n/help – Yardım"
                    )
                else:
                    tg_send_message("Anlaşılmadı. /scan veya /help deneyin.")
        except requests.exceptions.ReadTimeout:
            continue
        except Exception:
            time.sleep(2)
            continue


if __name__ == "__main__":
    # CLI: python telegram_bot_runner.py scan [aggressive]
    if len(sys.argv) > 1 and sys.argv[1].lower() in {"scan", "once"}:
        aggr = any(a.lower() in {"aggressive", "--aggressive", "aggr", "a"} for a in sys.argv[2:])
        run_scan_and_report(aggressive=aggr)
        sys.exit(0)
    print("Telegram bot runner başlatılıyor… /scan komutunu Telegram'dan gönderin.")
    try:
        poll_updates()
    except KeyboardInterrupt:
        print("Kapatılıyor (Ctrl+C)")
        sys.exit(0)
