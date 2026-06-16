"""
Finance Academy — Pipeline Çalıştırıcı
========================================
API sunucusu olmadan sadece agent pipeline'ını çalıştırır.
uvicorn / fastapi gerekmez.

Kullanım:
    cd Borsa/FinanceAcademy
    python run.py                  # tam pipeline (seed + daily + rapor)
    python run.py --seed           # sadece başlangıç içeriği yükle
    python run.py --daily          # günlük agent pipeline
    python run.py --weekly         # haftalık rapor
    python run.py --dashboard mericbsk  # kullanıcı dashboard
    python run.py --lesson TA-001-grafik-tipleri  # tek ders göster
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s — %(message)s")


def _print_llm_status():
    """Başlangıçta LLM durumunu göster."""
    import os

    from academy.agents.content_generator import _list_ollama_models, _load_env

    _load_env()

    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    groq_key = os.environ.get("GROQ_API_KEY", "")
    provider = os.environ.get("LLM_PROVIDER", "auto")

    print("┌─ LLM Durumu " + "─" * 40)
    models = _list_ollama_models(ollama_url)
    if models:
        chosen = ollama_model if ollama_model in models else models[0]
        print(f"│  🦙 Ollama  : ✅ {chosen}")
        print(f"│     Mevcut  : {', '.join(models)}")
    else:
        print(f"│  🦙 Ollama  : ⚠️  {ollama_url} — yanıt yok")

    if groq_key:
        print(f"│  ☁️  Groq    : ✅ key var ({groq_key[:8]}...)")
    else:
        print("│  ☁️  Groq    : ⚠️  key yok")

    active = "Ollama" if models else ("Groq" if groq_key else "Mock")
    print(f"│  Aktif      : {active}  (LLM_PROVIDER={provider})")
    print("└" + "─" * 53)
    print()


def main():
    parser = argparse.ArgumentParser(description="Finance Academy CLI")
    parser.add_argument("--seed", action="store_true", help="Başlangıç içeriği yükle")
    parser.add_argument("--daily", action="store_true", help="Günlük pipeline")
    parser.add_argument("--weekly", action="store_true", help="Haftalık rapor")
    parser.add_argument("--dashboard", metavar="USER_ID", help="Kullanıcı dashboard")
    parser.add_argument("--lesson", metavar="LESSON_ID", help="Ders detayı göster")
    parser.add_argument("--status", action="store_true", help="Sistem durumu")
    parser.add_argument("--onboard", metavar="USER_ID", help="Kullanıcı onboard et")
    args = parser.parse_args()

    _print_llm_status()

    from academy.orchestrator import AcademyOrchestrator

    orch = AcademyOrchestrator()

    if not any(vars(args).values()):
        # Hiç argüman yok → tam pipeline
        print("\n🎓 Finance Academy — Tam Pipeline\n")
        _run_full(orch)
        return

    if args.status:
        st = orch.system_status()
        print("\n📊 Sistem Durumu")
        print(f"  Yayınlanan ders : {st['total_published_lessons']}")
        print(f"  Bekleyen iş     : {st['pending_jobs']}")
        print(f"  Zaman           : {st['timestamp']}")
        print("\n  Domain bazında:")
        for d, n in st["by_domain"].items():
            print(f"    {d:<30} {n} ders")

    if args.seed:
        print("\n🌱 Başlangıç içeriği yükleniyor...")
        r = orch.seed_starter_content()
        print(f"  ✅ {r['inserted']} ders yüklendi, {r['skipped']} zaten vardı.")

    if args.daily:
        print("\n⚙️  Günlük pipeline çalışıyor...")
        r = orch.run_daily()
        print(f"  Gap tespit     : {r['gaps_found']}")
        print(f"  İş tamamlanan  : {r['jobs_processed']}")
        print(f"  İncelenen      : {r['reviewed']}")
        print(f"  Yayınlanan     : {r['published']}")

    if args.weekly:
        print("\n📅 Haftalık rapor hazırlanıyor...")
        r = orch.run_weekly()
        print(orch.analytics.format_report_text(r))

    if args.onboard:
        print(f"\n👤 {args.onboard} onboard ediliyor...")
        result = orch.onboard_user(
            args.onboard,
            {
                "experience": "beginner",
                "focus": "swing_trading",
                "time": 15,
            },
        )
        print(f"  Hedef     : {result['primary_goal']}")
        print(f"  Sonraki   : {result['next_lessons'][:3]}")

    if args.dashboard:
        print(f"\n📱 {args.dashboard} Dashboard\n")
        dash = orch.get_user_dashboard(args.dashboard)
        print(f"  Streak         : {dash['streak']} gün")
        print(f"  Toplam ders    : {dash['total_lessons']}")
        print(f"  Engagement     : {dash['engagement_score']:.1f}/100")
        print("\n  Sonraki dersler:")
        for l in dash["next_lessons"]:
            print(f"    → [{l['difficulty']:12}] {l['title'][:50]} ({l['estimated_minutes']}dk)")
        card = dash["daily_card"]
        print(f"\n  Bugünkü görev  : {card['next_lesson']['title']}")
        print(f"  Motivasyon     : {card['motivation']}")

    if args.lesson:
        from academy.models import LessonComponentRepository, LessonRepository

        lesson = LessonRepository().get(args.lesson)
        if not lesson:
            print(f"❌ '{args.lesson}' bulunamadı")
            return
        comps = LessonComponentRepository().get_for_lesson(args.lesson)
        quizzes = [c for c in comps if c["type"] == "quiz"]
        flashcards = [c for c in comps if c["type"] == "flashcard"]
        print(f"\n{'='*60}")
        print(f"  {lesson.title}")
        print(
            f"  [{lesson.domain}] {lesson.module} | {lesson.difficulty} | {lesson.estimated_minutes}dk"
        )
        print(f"{'='*60}\n")
        print(lesson.content)
        print(f"\n{'─'*60}")
        print("🎯 Kilit Çıkarımlar:")
        for t in lesson.key_takeaways:
            print(f"  • {t}")
        print("\n⚠️  Yaygın Yanlış Anlamalar:")
        for m in lesson.misconceptions:
            print(f"  • {m}")
        if quizzes:
            print(f"\n🧠 Quiz ({len(quizzes)} soru):")
            for i, q in enumerate(quizzes, 1):
                c = q["content"]
                print(f"  {i}. {c['question']}")
                for opt in c.get("options", []):
                    marker = "✓" if opt.startswith(c.get("correct", "")) else " "
                    print(f"     [{marker}] {opt}")
        if flashcards:
            print(f"\n📇 Flashcards ({len(flashcards)} adet):")
            for c in flashcards:
                fc = c["content"]
                print(f"  Q: {fc['front']}")
                print(f"  A: {fc['back']}\n")


def _run_full(orch):
    """Tam kurulum ve test."""
    from academy.models import LessonRepository

    stats = LessonRepository().stats()

    if stats["total_published"] == 0:
        print("🌱 İlk kurulum — başlangıç içeriği yükleniyor...")
        r = orch.seed_starter_content()
        print(f"   {r['inserted']} ders yüklendi\n")

    print("⚙️  Günlük pipeline...")
    daily = orch.run_daily()
    print(f"   Gap: {daily['gaps_found']}  |  Yayınlanan: {daily['published']}\n")

    print("📅 Haftalık rapor:")
    weekly = orch.run_weekly()
    print(orch.analytics.format_report_text(weekly))

    print("📊 Güncel durum:")
    st = orch.system_status()
    print(f"   Toplam yayınlanan ders : {st['total_published_lessons']}")
    for d, n in st["by_domain"].items():
        print(f"     {d:<35} {n} ders")


if __name__ == "__main__":
    main()
