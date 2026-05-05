# 2Y Profile Backtest Report

Bu rapor, iki stratejiyi ayni gunluk proxy backtest mantigiyla karsilastirir.
Canli MTF runtime birebir replay edilmedi; bunun yerine mevcut sade backtest mantigi uzerine iki profil uygulandi.

## Kapsam
- Donem: 2024-04-19 -> 2026-04-18
- Gun sayisi: 730
- Istenen sembol: 202
- Kullanilan sembol: 197
- Atlanan sembol: 4

## Kisa Yorum
- Eski strateji, toplam getiride yeni adaydan daha iyi gorunuyor.
- Yeni aday daha az geri cekilme yasiyor; risk daha kontrollu.
- Yeni aday daha secici; daha az islem aciyor.

## Metrik Farki
- Toplam getiri: 953.62% -> 602.29% (-351.33%)
- Final sermaye: 105362.11 -> 70228.91 (-35133.2)
- Gerceklesen islem: 1791 -> 1626 (-165)
- Bulunan sinyal: 9930 -> 8069 (-1861)
- Kazanma orani: 43.94% -> 43.79% (-0.15%)
- Profit factor: 1.39 -> 1.35 (-0.04)
- Islem basi ortalama PnL: 53.25 -> 37.04 (-16.21)
- Ortalama bekleme suresi: 34.61 gun -> 34.4 gun (-0.21 gun)
- Yilliklandirilmis getiri: 225.65% -> 165.72% (-59.93%)
- Sharpe: 2.24 -> 2.05 (-0.19)
- Max drawdown: 43.46% -> 38.76% (-4.7%)

## Giris Farki
- Candidate tarafindan eklenen giris: 166
- Candidate tarafindan cikartilan giris: 331
- Ortak giris orani: 85.46%

## En Cok Eklenen Semboller
```json
{
  "XLP": 7,
  "ADP": 5,
  "HYG": 4,
  "VNQ": 4,
  "BATRK": 4,
  "QQQ": 4,
  "NEE": 4,
  "ACRS": 4,
  "PG": 3,
  "RTX": 3,
  "AVBP": 3,
  "SHEL": 3,
  "TLT": 3,
  "INTU": 3,
  "ABAT": 3
}
```

## En Cok Cikarilan Semboller
```json
{
  "ACR": 12,
  "LMAT": 11,
  "BATRA": 11,
  "AEI": 11,
  "AFBI": 9,
  "AAME": 9,
  "HYG": 8,
  "ACTG": 8,
  "BATRK": 8,
  "AFRI": 8,
  "AVBP": 8,
  "XLP": 7,
  "ABP": 6,
  "AEYE": 6,
  "AACG": 6
}
```

## Not
- Bu calisma, mevcut rollout incelemesiyle tutarlilik icin gunluk proxy kullaniyor.
- Yani sonuc, canlidaki tum intraday detaylari degil; ayni veri tabani uzerindeki iki profil farkini gosteriyor.
- Gercek canli esdegerlik icin bir sonraki adim runtime threshold refactor ve shadow replay olmali.
