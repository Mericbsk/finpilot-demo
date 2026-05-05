# 🤖 DRL Araştırma Raporu — 2026-W15
*Oluşturuldu: 2026-04-08 12:15 UTC | İterasyon: 4*

---

## 📊 Top 5 Model — Mevcut Durum

| # | Model | Sharpe | Return | MaxDD | Trades | Skor | Sorunlar |
|---|-------|--------|--------|-------|--------|------|----------|
| 1 | ppo_trend | 0.0570 | 574% | 47% | 149 | 4.27 | 🔴DD |
| 2 | ppo_trend | 0.0527 | 353% | 38% | 128 | 3.33 | 🔴DD |
| 3 | ppo_momentum | 0.0629 | 300% | 47% | 458 | 2.23 | 🔴DD 🟡OT |
| 4 | ppo_trend | 0.0426 | 270% | 47% | 81 | 2.16 | 🔴DD 🟡SH |
| 5 | ppo_momentum | 0.0554 | 211% | 41% | 505 | 1.80 | 🔴DD 🟡OT |

**Lejand:** 🔴DD=Yüksek MaxDD | 🟡OT=Overtrading | 🟡SH=Düşük Sharpe | 🔴NR=Negatif Return

### ⚠️ Çeşitlilik Uyarısı
> Top 5 içinde yalnızca 2 farklı ajan türü var. 'trend' baskın (3/5). Ensemble için çeşitlilik önerisi: conservative veya swing modeli ekle.

## 🔍 Tespit Edilen Ortak Sorunlar

- 🔴 KRİTİK **high_dd** (#[1, 2, 3, 4, 5]): Top 5'in tamamında MaxDD >%35

## 💡 Önerilen Müdahaleler (Öncelik Sırasına Göre)

### 1. dd_weight — 5/5 model (#[1, 2, 3, 4, 5])
**Sorun:** `high_dd`
**Mevcut değer:** `0.3`
**Önerilen değer:** `0.8`
**Optuna arama aralığı:** `(0.5, 2.0)`

> MaxDD >35% → dd_weight artırılmalı (0.3→0.8). Model DD'yi görmezden geliyor çünkü ceza çok düşük.

## ⚡ Bu Hafta Çalıştırılacak Komutlar

### 🔴 KRİTİK ppo_trend
**Sorun:** `high_dd` — ppo_trend — MaxDD >35% → dd_weight artırılmalı (0.3→0.8). Mo...
**Beklenen iyileşme:** MaxDD %47 → tahmini %28 (dd_weight artışıyla ~%40 azalma bekleniyor)

```bash
# 1. Adım: Optuna ile optimum parametreyi bul (~30 dakika)
python scripts/optuna_trio.py --agent trend --n-trials 15 --dd-weight 0.8

# 2. Adım: En iyi parametre ile yeniden eğit (~2-4 saat)
python scripts/retrain_models.py --only trend --dd-weight 0.8
```

### 🔴 KRİTİK ppo_trend
**Sorun:** `high_dd` — ppo_trend — MaxDD >35% → dd_weight artırılmalı (0.3→0.8). Mo...
**Beklenen iyileşme:** MaxDD %38 → tahmini %23 (dd_weight artışıyla ~%40 azalma bekleniyor)

```bash
# 1. Adım: Optuna ile optimum parametreyi bul (~30 dakika)
python scripts/optuna_trio.py --agent trend --n-trials 15 --dd-weight 0.8

# 2. Adım: En iyi parametre ile yeniden eğit (~2-4 saat)
python scripts/retrain_models.py --only trend --dd-weight 0.8
```

### 🔴 KRİTİK ppo_momentum
**Sorun:** `high_dd` — ppo_momentum — MaxDD >35% → dd_weight artırılmalı (0.3→0.8)....
**Beklenen iyileşme:** MaxDD %47 → tahmini %28 (dd_weight artışıyla ~%40 azalma bekleniyor)

```bash
# 1. Adım: Optuna ile optimum parametreyi bul (~30 dakika)
python scripts/optuna_trio.py --agent momentum --n-trials 15 --dd-weight 0.8

# 2. Adım: En iyi parametre ile yeniden eğit (~2-4 saat)
python scripts/retrain_models.py --only momentum --dd-weight 0.8
```

### 🔴 KRİTİK ppo_trend
**Sorun:** `high_dd` — ppo_trend — MaxDD >35% → dd_weight artırılmalı (0.3→0.8). Mo...
**Beklenen iyileşme:** MaxDD %47 → tahmini %28 (dd_weight artışıyla ~%40 azalma bekleniyor)

```bash
# 1. Adım: Optuna ile optimum parametreyi bul (~30 dakika)
python scripts/optuna_trio.py --agent trend --n-trials 15 --dd-weight 0.8

# 2. Adım: En iyi parametre ile yeniden eğit (~2-4 saat)
python scripts/retrain_models.py --only trend --dd-weight 0.8
```

### 🔴 KRİTİK ppo_momentum
**Sorun:** `high_dd` — ppo_momentum — MaxDD >35% → dd_weight artırılmalı (0.3→0.8)....
**Beklenen iyileşme:** MaxDD %41 → tahmini %25 (dd_weight artışıyla ~%40 azalma bekleniyor)

```bash
# 1. Adım: Optuna ile optimum parametreyi bul (~30 dakika)
python scripts/optuna_trio.py --agent momentum --n-trials 15 --dd-weight 0.8

# 2. Adım: En iyi parametre ile yeniden eğit (~2-4 saat)
python scripts/retrain_models.py --only momentum --dd-weight 0.8
```

## 📈 Geçmiş Optuna Sonuçları

- **momentum**: 0 trial | En iyi skor: `0.1906` | Bulgu: Yüksek pnl_weight (20.1) → agresif return odağı
- **conservative**: 0 trial | En iyi skor: `0.0702` | Bulgu: dd_weight=0.53 → DD kontrolü aktif, MaxDD düşüyor
- **range**: 0 trial | En iyi skor: `0.0641` | Bulgu: dd_weight=0.62 → DD kontrolü aktif, MaxDD düşüyor
- **swing**: 0 trial | En iyi skor: `0.0414` | Bulgu: Yüksek pnl_weight (17.4) → agresif return odağı

## 🎯 Sonraki Adım

```
Optuna ile 'dd_weight' optimize et (önerilen: 0.8, aralık: (0.5, 2.0))
```

---
*Bu rapor `scripts/drl_autopilot.py` tarafından otomatik üretilmiştir.*
