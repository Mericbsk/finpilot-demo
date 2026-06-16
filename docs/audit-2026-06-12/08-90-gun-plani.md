# 90 Gün Uygulama Planı (2026-06-15 → 2026-09-13)

Teknik P0'lar + V6→V7→V10 vizyon zinciri + Academy (Bölüm H) tek takvimde.

## FAZ 1 — İSPAT (Gün 1-30)
**Hedef:** Güvenlik/temizlik P0'ları kapat, dağıtım kanalını aç, ilk dış kullanıcıları al.

Hafta 1 (teknik temizlik — toplam ~3 gün iş):
- [P0] Auth regresyonu: require_auth geri ekle, test yeşil (Sorun #3)
- [P0] FinanceAcademy/ → archive/; academy.db tekille; seed çalıştır (Sorun #2)
- [P1] Landing + waitlist sayfası canlı (Sorun #6)
- [P1] Skor bileşenlerini ablation'a göre yeniden ağırlıklandır + haftalık otomatik Edge Report job'u (Sorun #1 — kısa vade)

Hafta 2-3:
- V6: weekly_report → Beehiiv hattı; ilk 2 sayı yayında; build-in-public başlangıcı (X/LinkedIn)
- Academy: orchestrator'ı core scheduler'a bağla; ilk 20 ders üret + elle denetle (golden-set)
- Dashboard'a "Sistem Sağlığı" kartı (job-run + model yaşı) (Sorun #5)
- DRL model-yaşı guard'ı + üründe "deneysel" etiketi (Sorun #4 kısa vade)

Hafta 4:
- Academy router + dashboard sayfası + günlük kart (H.3)
- 20 kullanıcı görüşmesi (P6'nın şartı) — bülten abonelerinden

**Faz 1 başarı kriterleri:** Auth testi yeşil; bülten 2+ sayı, ≥100 abone; Academy'de 1 kullanıcı ders+quiz tamamlıyor; Edge Report otomatik üretiliyor.

## FAZ 2 — ÖLÇEK (Gün 31-60)
**Hedef:** Kanıtlanan kanalı büyüt, V7 copilot beta.

- V7: 3-soru onboarding + günlük kişisel brief (web + Telegram); waitlist'ten 20 concierge beta
- V6: bülten premium katmanı aç ($8-12); public track-record/karne sayfası
- Academy: Trend Scout agent (A5) + Analytics→kpi_tracker; 60+ ders yayında
- Teknik: watchlist.py servisleştirme; tek ROADMAP.md + docs temizliği (Sorun #7); CI güncelle
- Karar noktası (gün 60): Edge Report 4 haftalık trend — pozitifleşiyorsa V1 hazırlığı; değilse sinyal iddiası vitrinden tamamen çıkar

**Başarı:** 500+ bülten abonesi; 20 beta'nın ≥10'u haftada 4+ gün brief açıyor; ilk ödeme alındı (premium bülten veya lifetime deal).

## FAZ 3 — SİSTEM (Gün 61-90)
**Hedef:** İnsan müdahalesini minimize et, V10'u aç, geliri stack'le.

- V10: portföy girişi (manuel/CSV) + bağlam-bilen uyarılar + freemium sınırı (3 pozisyon)
- V7 genel açılış: $9-15/ay premium
- Academy: Examiner/Simulator (A8, signals_archive senaryolarıyla); 150+ ders; "ders→davranış" metriği canlı
- Otomasyon denetimi: tüm tekrar eden işler cron'da; haftalık insan emeği ölç (<5 saat hedef)
- Hibe paraleli (opsiyonel): FINANZPLAN'ı güncel sistemle yenile, akademik danışman araması

**Başarı (gün 90):** Haftada ≤5 saat insan emeğiyle: 1.500+ liste, 30-80 ödeyen abone ($300-1.000 MRR başlangıcı), Academy tam otonom haftalık üretimde, Edge Report kararı verilmiş (V1 aç/kapat).

## SÜREKLİ KURALLAR (önleme mekanizmaları)
1. Yeni skor bileşeni → edge testi geçmeden merge yok.
2. Yeni modül → router+UI+test+doc olmadan "bitti" sayılmaz (Academy dersi).
3. Güvenlik test fail'i → 72 saat SLA, baseline'a giremez.
4. Her belge "supersedes:" satırı taşır; çeyrek başına docs küratörlüğü.
5. Her yeni özellik şu sorudan geçer: "Kullanıcı-özel veri biriktiriyor mu?" (P12 testi).
