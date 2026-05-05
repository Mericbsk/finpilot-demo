# 2Y Profile Backtest Report

Bu rapor, iki stratejiyi ayni gunluk proxy backtest mantigiyla karsilastirir.
Canli MTF runtime birebir replay edilmedi; bunun yerine mevcut sade backtest mantigi uzerine iki profil uygulandi.

## Kapsam
- Donem: 2025-10-01 -> 2025-12-31
- Gun sayisi: 92
- Istenen sembol: 20
- Kullanilan sembol: 20
- Atlanan sembol: 0

## Kisa Yorum
- Yeni aday strateji, toplam getiride eski stratejiyi geciyor.
- Yeni aday daha az geri cekilme yasiyor; risk daha kontrollu.
- Yeni aday daha secici; daha az islem aciyor.

## Metrik Farki
- Toplam getiri: -2.61% -> -0.86% (+1.75%)
- Final sermaye: 9739.28 -> 9913.55 (+174.27)
- Gerceklesen islem: 31 -> 28 (-3)
- Bulunan sinyal: 110 -> 102 (-8)
- Kazanma orani: 38.71% -> 42.86% (+4.15%)
- Profit factor: 0.8 -> 0.92 (+0.12)
- Islem basi ortalama PnL: -8.41 -> -3.09 (+5.32)
- Ortalama bekleme suresi: 28.35 gun -> 30.43 gun (+2.08 gun)
- Yilliklandirilmis getiri: -18.8% -> -12.81% (+5.99%)
- Sharpe: -2.19 -> -1.55 (+0.64)
- Max drawdown: 7.33% -> 6.4% (-0.93%)

## Giris Farki
- Candidate tarafindan eklenen giris: 0
- Candidate tarafindan cikartilan giris: 3
- Ortak giris orani: 94.92%

## En Cok Eklenen Semboller
```json
{}
```

## En Cok Cikarilan Semboller
```json
{
  "ORCL": 1,
  "WDAY": 1,
  "ARM": 1
}
```

## Not
- Bu calisma, mevcut rollout incelemesiyle tutarlilik icin gunluk proxy kullaniyor.
- Yani sonuc, canlidaki tum intraday detaylari degil; ayni veri tabani uzerindeki iki profil farkini gosteriyor.
- Gercek canli esdegerlik icin bir sonraki adim runtime threshold refactor ve shadow replay olmali.
