"""Telegram Bot Runner — public bot + admin ops.

Public commands (any user, replies go to the sender's chat):
    /start     kayıt + tanıtım + kanal linki
    /today     son yayınlanan brifi DM'e iletir
    /feedback  serbest metin geri bildirim (sonraki mesaj kaydedilir)
    /premium   premium ilgi kaydı ("yakında")
    /help      komut listesi

Admin-only (TELEGRAM_ADMIN_ID / legacy CHAT_ID):
    /scan [aggressive]   taramayı çalıştırır, CSV döner (mevcut davranış)
    ONAYLA <id>          broadcast kuyruğundaki taslağı onaylar
    RED <id>             taslağı reddeder
    /bekleyen            bekleyen taslakları listeler

Distribution katmanı (kuyruk, kullanıcı kaydı, teslimat logu) için
``distribution/`` modülünü kullanır; modül yoksa eski davranışa düşer.
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
ADMIN_ID = str(os.getenv("TELEGRAM_ADMIN_ID", "") or CHAT_ID)
CHANNEL_LINK = os.getenv("TELEGRAM_CHANNEL_LINK", "")  # t.me/... (public kanal)
SITE_URL = os.getenv("FINPILOT_SITE_URL", "https://www.finpilot.at")

DISCLAIMER = (
    "Bu bot araştırma ve eğitim amaçlıdır; yatırım tavsiyesi vermez. "
    "Geçmiş performans gelecek sonuçların garantisi değildir."
)

# /feedback akışı: kullanıcıdan bir sonraki mesajı bekleyenler
_awaiting_feedback: set[str] = set()

try:
    from distribution import broadcast as _bq
    from distribution.store import (
        bump_premium_interest,
        log_tg_feedback,
        upsert_tg_user,
    )

    _DIST = True
except Exception:  # pragma: no cover - distribution katmanı opsiyonel
    _DIST = False


def tg_send_message(text: str, chat_id: str | None = None):
    """Mesaj gönder. chat_id verilmezse admin'e gider (legacy davranış)."""
    try:
        resp = requests.post(
            f"{API_BASE}/sendMessage",
            json={
                "chat_id": chat_id or CHAT_ID,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        return resp.ok
    except Exception:
        return False


def tg_send_document(file_path: str, caption: str = "", chat_id: str | None = None):
    try:
        with open(file_path, "rb") as f:
            resp = requests.post(
                f"{API_BASE}/sendDocument",
                data={"chat_id": chat_id or CHAT_ID, "caption": caption},
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
    if not os.path.exists(os.path.join(cwd, "scanner.py")):
        tg_send_message(
            "⚠️ scanner.py bu dizinde yok — /scan CLI yolu devre dışı. "
            "Taramayı dashboard'dan (http://localhost:3001) veya API üzerinden çalıştır; "
            "sonuçlar distribution export'una otomatik düşer."
        )
        return
    tg_send_message("🔎 Tarama başlatıldı. Lütfen bekleyin…" + (" (Agresif)" if aggressive else ""))
    start = time.time()

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

    if csv_path and os.path.exists(csv_path):
        summary = summarize_csv(csv_path)
        tg_send_message(
            f"✅ Tarama tamamlandı ({elapsed:.1f}s){' · Agresif' if aggressive else ''}\n\n{summary}"
        )
        tg_send_document(csv_path, caption=os.path.basename(csv_path))
    else:
        tg_send_message(f"✅ Tarama tamamlandı ({elapsed:.1f}s)\n\nCSV dosyası bulunamadı.")

    if sug_path and os.path.exists(sug_path):
        sug_summary = summarize_suggestions(sug_path, limit=10)
        tg_send_message(sug_summary)
        tg_send_document(sug_path, caption=os.path.basename(sug_path))


# ── Public komutlar ──────────────────────────────────────────────────────────


def _cmd_start(chat_id: str, username: str) -> None:
    if _DIST:
        upsert_tg_user(chat_id, username=username, source="bot_start")
    kanal = f"\n📣 Günlük brif kanalı: {CHANNEL_LINK}" if CHANNEL_LINK else ""
    tg_send_message(
        "👋 Merhaba! Ben FinPilot botuyum.\n\n"
        "Her sabah 1.800+ hisse taranır; dikkat çeken adaylar gerekçeleriyle ve "
        "sistemin AÇIK karnesiyle paylaşılır. Günde 1 mesaj — o kadar.\n"
        f"{kanal}\n"
        f"🔍 Dünün brifini web'de gör: {SITE_URL}/demo\n\n"
        "Komutlar: /today /feedback /premium /help\n\n"
        f"ℹ️ {DISCLAIMER}",
        chat_id=chat_id,
    )


def _cmd_today(chat_id: str) -> None:
    if _DIST:
        last = _bq.get_last_sent("daily")
        if last:
            tg_send_message(last["text"], chat_id=chat_id)
            return
    tg_send_message(
        f"Henüz yayınlanmış bir brif yok. Kanala katıl: {CHANNEL_LINK or SITE_URL}",
        chat_id=chat_id,
    )


def _cmd_feedback(chat_id: str) -> None:
    _awaiting_feedback.add(chat_id)
    tg_send_message(
        "📝 Dinliyorum — bir sonraki mesajını geri bildirim olarak kaydedeceğim. "
        "(En yararlı/en kafa karıştıran ne, ne eksik?)",
        chat_id=chat_id,
    )


def _cmd_premium(chat_id: str) -> None:
    n = bump_premium_interest(chat_id) if _DIST else 0
    tg_send_message(
        "💠 Premium (tam aday listesi + derin gerekçe + risk notları) hazırlanıyor. "
        "İlgini kaydettim — ilk açılışta buradan haber vereceğim. "
        "O zamana kadar ücretsiz brif ve açık karne her sabah seninle.\n\n"
        f"ℹ️ {DISCLAIMER}",
        chat_id=chat_id,
    )
    if n == 1 and ADMIN_ID:
        tg_send_message(f"📈 Yeni premium ilgisi: {chat_id}", chat_id=ADMIN_ID)


def _cmd_help(chat_id: str, is_admin: bool) -> None:
    lines = [
        "Komutlar:",
        "/start — tanıtım + kanal linki",
        "/today — son yayınlanan brif",
        "/feedback — geri bildirim bırak",
        "/premium — premium hakkında",
    ]
    if is_admin:
        lines += [
            "— admin —",
            "/scan [aggressive] — tarama",
            "/bekleyen — onay bekleyen taslaklar",
            "ONAYLA <id> / RED <id> — taslak kararı",
        ]
    lines.append(f"\nℹ️ {DISCLAIMER}")
    tg_send_message("\n".join(lines), chat_id=chat_id)


# ── Admin komutları ──────────────────────────────────────────────────────────


def _cmd_pending(chat_id: str) -> None:
    if not _DIST:
        tg_send_message("distribution modülü yüklü değil.", chat_id=chat_id)
        return
    pending = _bq.get_pending()
    if not pending:
        tg_send_message("✅ Bekleyen taslak yok.", chat_id=chat_id)
        return
    for p in pending:
        tg_send_message(
            f"#{p['id']} [{p['kind']}] {p['brief_date']}\n\n{p['text'][:1200]}\n\n"
            f"ONAYLA {p['id']}  /  RED {p['id']}",
            chat_id=chat_id,
        )


def _cmd_decide(chat_id: str, text: str) -> None:
    if not _DIST:
        tg_send_message("distribution modülü yüklü değil.", chat_id=chat_id)
        return
    parts = text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        tg_send_message("Kullanım: ONAYLA <id>  veya  RED <id>", chat_id=chat_id)
        return
    qid = int(parts[1])
    approve = parts[0].upper().startswith("ONAY")
    ok = _bq.decide(qid, approve=approve, decided_by=chat_id)
    if ok:
        tg_send_message(
            ("✅ Onaylandı" if approve else "🚫 Reddedildi")
            + f": #{qid}. "
            + ("Yayın saati geldiğinde kanala gönderilecek." if approve else ""),
            chat_id=chat_id,
        )
    else:
        tg_send_message(f"#{qid} bulunamadı ya da zaten karar verilmiş.", chat_id=chat_id)


# ── Ana döngü ────────────────────────────────────────────────────────────────


def handle_message(chat_id: str, username: str, text: str) -> None:
    """Tek mesajı işle (test edilebilir saf giriş noktası)."""
    is_admin = chat_id == ADMIN_ID
    low = text.lower()

    # feedback follow-up
    if chat_id in _awaiting_feedback and not low.startswith("/"):
        _awaiting_feedback.discard(chat_id)
        if _DIST:
            log_tg_feedback(chat_id, text[:2000])
        tg_send_message(
            "🙏 Teşekkürler — kaydettim. Her Cuma hepsini tek tek okuyorum.", chat_id=chat_id
        )
        if ADMIN_ID and chat_id != ADMIN_ID:
            tg_send_message(f"💬 Yeni feedback ({chat_id}): {text[:500]}", chat_id=ADMIN_ID)
        return

    if low.startswith("/start") or low == "start":
        _cmd_start(chat_id, username)
    elif low.startswith("/today"):
        _cmd_today(chat_id)
    elif low.startswith("/feedback"):
        _cmd_feedback(chat_id)
    elif low.startswith("/premium"):
        _cmd_premium(chat_id)
    elif low.startswith("/help"):
        _cmd_help(chat_id, is_admin)
    elif low.startswith("/bekleyen"):
        if is_admin:
            _cmd_pending(chat_id)
        else:
            tg_send_message("Bu komut yalnız yönetici içindir.", chat_id=chat_id)
    elif text.upper().startswith(("ONAYLA", "RED")):
        if is_admin:
            _cmd_decide(chat_id, text)
        else:
            tg_send_message("Bu komut yalnız yönetici içindir.", chat_id=chat_id)
    elif low.startswith("/scan"):
        if not is_admin:
            tg_send_message(
                "Bu komut yalnız yönetici içindir. /help ile komutları gör.", chat_id=chat_id
            )
            return
        tokens = low.split()
        is_aggr = any(t in ("aggressive", "--aggressive", "aggr", "a") for t in tokens[1:])
        run_scan_and_report(aggressive=is_aggr)
    else:
        tg_send_message("Anlaşılmadı. /help ile komutları görebilirsin.", chat_id=chat_id)


def poll_updates():
    if ADMIN_ID:
        tg_send_message("🤖 Bot hazır. /help ile komutları görebilirsin.", chat_id=ADMIN_ID)
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
                chat = msg.get("chat", {})
                if chat.get("type") != "private":
                    continue  # kanal/grup mesajlarını yoksay — bot yalnız DM'de konuşur
                chat_id = str(chat.get("id"))
                username = str(msg.get("from", {}).get("username") or "")
                text = (msg.get("text") or "").strip()
                if not text:
                    continue
                try:
                    handle_message(chat_id, username, text)
                except Exception as exc:  # tek mesaj hatası döngüyü öldürmesin
                    if ADMIN_ID:
                        tg_send_message(f"⚠️ Bot hata: {exc}", chat_id=ADMIN_ID)
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
    print("Telegram bot runner başlatılıyor… /help komutunu Telegram'dan gönderin.")
    try:
        poll_updates()
    except KeyboardInterrupt:
        print("Kapatılıyor (Ctrl+C)")
        sys.exit(0)
