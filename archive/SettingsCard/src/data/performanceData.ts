import type { PerformanceDataset, TarihAraligi } from "../types/performance";

export const performanceData: PerformanceDataset = {
  kpi: {
    basariOraniYuzde: 74,
    basariOraniTrend: [0.68, 0.7, 0.72, 0.74],
    ortalamaNetGetiriYuzde: 12.5,
    ortalamaNetGetiriTrend: [8.2, 9.7, 11.4, 12.5],
    netKarZararUSD: 15420,
    netKarZararTrend: [9200, 11800, 13750, 15420]
  },
  gecmisSinyaller: [
    {
      id: "2025-09-12-AAPL",
      tarih: "2025-09-12",
      sembol: "AAPL",
      sinyal: "AL",
      rrOrani: 2.7,
      kapanisFiyati: 191.32,
      netGetiriYuzdesi: 8.2,
      durum: "Başarılı",
      tldr: "Momentum güçlü, bilanço sonrası yükseliş.",
      grafikNotu: "Eylül ortasında gap'li açılış ve MA50 kırılımı."
    },
    {
      id: "2025-09-20-TSLA",
      tarih: "2025-09-20",
      sembol: "TSLA",
      sinyal: "SAT",
      rrOrani: 1.1,
      kapanisFiyati: 222.18,
      netGetiriYuzdesi: -3.5,
      durum: "Başarısız",
      tldr: "Volatilite yüksek, regülasyon baskısı.",
      grafikNotu: "Tepede hacim artışı, RSI negatif uyumsuzluk."
    },
    {
      id: "2025-10-01-META",
      tarih: "2025-10-01",
      sembol: "META",
      sinyal: "AL",
      rrOrani: 2.1,
      kapanisFiyati: 318.74,
      netGetiriYuzdesi: 5.6,
      durum: "Başarılı",
      tldr: "Reklam gelirleri beklentiyi aştı, trend devam ediyor.",
      grafikNotu: "EMA 21 destek, hacim artan kanal içinde."
    },
    {
      id: "2025-08-18-MSFT",
      tarih: "2025-08-18",
      sembol: "MSFT",
      sinyal: "BEKLE",
      rrOrani: 1.5,
      kapanisFiyati: 409.55,
      netGetiriYuzdesi: 0.4,
      durum: "Açık Pozisyon",
      tldr: "Yeni ürün lansmanı öncesi konsolidasyon.",
      grafikNotu: "Sideways range, Bollinger band daralması."
    }
  ],
  altBolumIpuclari: [
    {
      tip: "STRATEJI_HATIRLATMA",
      baslik: "Kural Basit",
      icerik: "Yeşil sinyalleri (AL) R/R Oranına göre filtrele, Stop-Loss ve Take-Profit belirleyerek bekle.",
      terimEslestirme: ["R/R Oranı", "Stop-Loss", "Take-Profit"],
      oncelik: 1,
      baglanti: {
        etiket: "FinSense: R/R rehberi",
        url: "https://finsense.ai/rr-guide"
      }
    },
    {
      tip: "AKSIYON_IPUCU",
      baslik: "R/R Oranı Kontrolü",
      icerik: "PilotShield, R/R > 2.0 olan sinyallere odaklanmanızı önerir. Bu, riskinize karşılık gelen ödül potansiyelinizin 2 katından fazla olduğu anlamına gelir.",
      oncelik: 2
    },
    {
      tip: "AKSIYON_IPUCU",
      baslik: "Piyasalar Kapalıyken",
      icerik: "Piyasalar kapalıyken bile Ayarlar Panelinizi kontrol edin. Açık pozisyonlarınız için stop-loss emirlerini güncel tutmayı unutmayın.",
      oncelik: 3
    },
    {
      tip: "EGITIM_CTA",
      baslik: "Eğitim Modülüne Git",
      icerik: "Kararlarınızın arkasındaki Derin Pekiştirmeli Öğrenme (DRL) motorunun nasıl çalıştığını öğrenmek için PilotEDU'yu ziyaret edin.",
      oncelik: 4,
      baglanti: {
        etiket: "PilotEDU'ya Git",
        url: "https://finsense.ai/pilotedu"
      }
    }
  ],
  pilotChecklist: [
    {
      id: "filter-green",
      icerik: "Yeşil (AL) sinyalleri filtrele",
      aciklama: "Kazananları önce listele, momentum senden yana olsun."
    },
    {
      id: "focus-rr",
      icerik: "R/R > 2.0 olan fırsatlara odaklan",
      aciklama: "Risk başına ödülün iki katından fazla olduğuna emin ol."
    },
    {
      id: "set-stops",
      icerik: "Stop-Loss ve Take-Profit seviyeni kaydet",
      aciklama: "Giriş yapmadan önce çıkış planın hazır olsun."
    }
  ]
};

export const DATE_RANGE_OPTIONS: TarihAraligi[] = ["Son 30 Gün", "Son 90 Gün", "Tüm Zamanlar"];
