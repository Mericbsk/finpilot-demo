# FINPILOT / FINSENSE — MASTER PROJECT REALITY & CONTINUITY AUDIT

**Sürüm:** 1.0 · **Tarih:** 2026-09-08 · **Durum:** AKTİF (Meriç onaylı)
**Amaç:** FinPilot/FinSense'in gerçek durumunu yeniden inşa etmek ve bundan sonraki çalışmanın nereden devam etmesi gerektiğini belirlemek.

Bu dosya FinPilot'un standart denetim çerçevesidir. Her büyük çalışma öncesi bu prompt kullanılır. Governance: `_instructions/00-core.md`, `AGENTS.md`, `docs/governance/decision-log.md` ile uyumludur; onları geçersiz kılmaz, tamamlar.

---

## TEMEL İLKE

> **ÖNCE PROJEYİ ANLA. SONRA DEĞERLENDİR. EN SON ÖNER.**

Mevcut sistemi anlamadan yeni mimari, özellik, agent, strateji veya roadmap önermek YASAKTIR.

## GERÇEKLİK HİYERARŞİSİ (kanıt önceliği)

1. Çalışan kod / sistem / runtime
2. Gerçek veri (DB, CSV, JSON, backtest)
3. Test / deney kanıtı
4. Güncel dokümantasyon
5. Eski dokümantasyon
6. Fikir / hipotez

**Kod ≠ Doküman → çelişki. Çalışan sistem ≠ eski doküman → çalışan sistem esas. Doğrulanamıyorsa → UNKNOWN. Tahmin etme.**

## ÜÇ FAZ

- **FAZ 1 — DISCOVERY:** "Projede gerçekte ne var?" (yeni özellik önerme yok)
- **FAZ 2 — EVALUATION:** "Hangisi çalışıyor, doğrulanmış, sorunlu?"
- **FAZ 3 — STRATEGY:** "Buradan sonra ne yapmalıyız?" (yalnızca önceki faz kanıtlarına dayanarak)

## STATUS TAKSONOMİSİ

🟢 WORKING · 🟢 VALIDATED · 🔵 FROZEN · 🟡 PARTIAL · 🟠 UNVALIDATED · 🔴 FAILED · ⚫ DEPRECATED · ⚪ PLANNED · ❓ UNKNOWN

**FROZEN ≠ COMPLETED.** Her frozen bölüm için: neden, tarih, karar, yeniden-açılma koşulu, bağımlılıklar.

## FINPILOT ≠ FINSENSE

- **FINPILOT:** market data, scanner, research, backtest, ranking, regime, entry, MFE/MAE, risk, execution, trading engine
- **FINSENSE:** Thinking Mirror, prediction, reasoning, calibration, user interaction, financial learning
- İki sistemi birleştirme. Bağlantı yalnızca kanıtla kurulur; varsayımsal bağlantılar PROPOSED/FUTURE.

## DATASET SEPARATION (kritik)

- **5.216** = signals_archive (barrier-captured)
- **46.581** = ayrı full-universe/MFE çalışması
- **111** = 46.581'de ≥%100 MFE gözlemleri
- **+%0,40** = 5.216'nın historical mean
- **+%100 MFE ≠ +%100 captured return**
- **historical ≠ live profit · backtest ≠ future guarantee**

## ÇIKTI SIRASI (Part A → T)

A. Executive Summary · B. Current Project Reality · C. FinPilot System Map · D. FinSense System Map · E. Module & Dependency Inventory · F. Completed/Working/Frozen/Partial Audit · G. Research & Experiment Ledger · H. Failure/Negative Knowledge Ledger · I. Data & Number Integrity Audit · J. Contradiction Report · K. Decision History · L. Current vs Target State · M. Keep/Change/Freeze/Kill/Test · N. Critical Unknowns · O. Priority Analysis · P. Anti-Roadmap · Q. Master Work Plan · R. GO/NO-GO Gates · S. One-Page Project State · T. Final Verdict

## MASTER PRINCIPLE

DO NOT BUILD ON ASSUMPTIONS. BUILD ON VERIFIED STATE. TEST WHAT IS UNKNOWN. PRESERVE WHAT IS VALID. DO NOT REPEAT WHAT HAS FAILED. DO NOT CONFUSE THE PLAN WITH THE PRODUCT. DO NOT CONFUSE THE VISION WITH THE EVIDENCE. FIRST UNDERSTAND. THEN AUDIT. THEN DECIDE. THEN BUILD.

---

*Tam prompt metni: bu dosyanın kaynak sürümü (2026-09-08 kullanıcı girdisi).*
