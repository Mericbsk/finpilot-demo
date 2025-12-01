# FinPilot Ayarlar Paneli

Modüler, React 18 ve Tailwind CSS tabanlı FinPilot ayarlar paneli. Kullanıcının risk iştahını, portföy büyüklüğünü, piyasa tercihini ve gelişmiş tarama parametrelerini tek ekranda yönetmesini sağlar.

## Özellikler

- 🎚️ **Risk İştahı eşiği** – Renk kodlu slider ile 1-10 arası risk profili seçimi.
- 💼 **Portföy konfigürasyonu** – Portföy büyüklüğü ve maksimum kayıp limiti, kayıp/Kelly önerisi ile birlikte.
- 🔁 **Strateji modları** – Dengeli ve agresif tarama modları arasında hızlı geçiş.
- 📈 **Gelişmiş göstergeler** – EMA, RSI, ATR gibi göstergeleri aç/kapat, zaman dilimi ve veri kaynağı seçimi.
- 📲 **Telegram bildirimleri** – Tek tuşla etkinleştir, chat ID giriş alanı ile.
- ♻️ **Zustand durum yönetimi** – Tüm ayarların merkezi ve typesafe şekilde saklanması.

## Teknolojiler

- [React 18](https://react.dev/) + [TypeScript](https://www.typescriptlang.org/)
- [Vite](https://vitejs.dev/) geliştirme ortamı
- [Tailwind CSS](https://tailwindcss.com/) ile modern UI
- [Zustand](https://github.com/pmndrs/zustand) durum deposu
- [Lucide](https://lucide.dev/) ikon seti

## Başlangıç

```powershell
npm install
npm run dev
```

- `npm run dev`: Vite geliştirme sunucusunu 5173 portunda başlatır.
- `npm run lint`: ESLint ile statik analiz yapar.
- `npm run build`: Tip kontrolünü çalıştırıp üretim paketini `dist/` içine alır.
- `npm run preview`: Üretim paketini lokal olarak önizler.

## Mimari

```text
src/
├─ components/      # Kart içindeki modüler bileşenler
├─ store/           # Zustand tabanlı ayar deposu
├─ types/           # SettingsType ve enum benzeri tanımlar
├─ styles/          # Tailwind giriş noktası
└─ App.tsx          # SettingsCard kapsayıcısı
```

## API Sözleşmesi Taslağı

Analiz Hikâyesi Kartı ve FinSense eğitim modülü aynı dili konuşsun diye, frontend ile backend arasında aşağıdaki JSON yapısı üzerinde uzlaştık. Bu veri modeli progressive disclosure katmanlarını, sözlük eşleşmelerini ve CTA akışını tek uç noktadan besler.

```json
{
	"signalId": "AAPL-20251015",
	"hisse": "AAPL",
	"sinyal": "AL",
	"rrOrani": 2.7,
	"katmanlar": {
		"tldr": "Apple güçlü nakit akışı ve servis gelirleriyle öne çıkıyor.",
		"nedenAlinmali": [
			"Servis gelirlerinde %15 yıllık büyüme",
			"Yeni AR/VR katalizörü henüz fiyatlanmadı",
			"50B$ üzeri net nakit pozisyonu"
		],
		"nedenSatilmali": [
			"F/K oranı 5 yıllık ortalamanın %18 üzerinde",
			"AB regülasyon riski (DMA)",
			"Çin pazarında rekabet baskısı"
		],
		"nedenSimdi": [
			"Son fiyat düzeltmesiyle 200 EMA seviyesine yaklaşım",
			"Yaklaşan bilanço sürprizi olasılığı"
		],
		"rrAnalizi": {
			"stopLoss": 173,
			"takeProfit": 194,
			"rrOrani": 2.7,
			"karar": "AL"
		}
	},
	"aciklamalar": {
		"duygusalBasliklar": {
			"nedenAlinmali": "✅ Kaçırılmaması Gereken Güçlü Yönler",
			"nedenSatilmali": "🛑 Sermayeyi Korumak İçin Kritik Riskler",
			"nedenSimdi": "🎯 Şimdi Giriş İçin Fırsat Penceresi",
			"rrAnalizi": "⚔️ Pilot’un Karar Özeti"
		}
	},
	"sozluk": [
		{ "terim": "200 EMA", "aciklama": "200 günlük üssel hareketli ortalama" },
		{ "terim": "F/K", "aciklama": "Fiyat/Kazanç oranı" }
	],
	"cta": {
		"mesaj": "Bu seviyede netliği portföyünüzdeki 5 hisse için de ister misiniz?",
		"buton": "Ücretsiz Portföy Analizi Talep Et",
		"hedef": "/premium/portfolio-analysis"
	}
}
```

> Not: Çok dillilik veya farklı aksiyon tipleri (örn. `NAVIGATE`, `OPEN_MODAL`) gereksinimi doğarsa `katmanlar` ve `cta` düğümleri bu alanlara özel alt anahtarlarla genişletilmeye uygundur.

### Backend Entegrasyon Sonraki Adımlar

- `GET /analysis/:symbol` şeklinde bir endpoint taslağı çıkarıp, `kullaniciDil`, `riskSkoru` gibi parametreleri sorgu dizgisi üzerinden alacak şekilde şemaya bağla.
- Çok dillilik için `katmanlar` ve `aciklamalar` altında `tr`, `en` gibi alt düğümlere destek ekle; olmayan dil için fallback mantığını sözleşmede belirt.
- `cta` nesnesine `aksiyonTipi` (`NAVIGATE`, `OPEN_MODAL`, `OPEN_TRADE_PANEL`) gibi enum değerleri ekleyerek frontend routing mantığıyla hizala.
- FinSense sözlüğüyle entegrasyon için `sozluk` terimlerini backend’de canonical bir sözlük servisine eşle; API tarafında eşleşme bulunamadığında graceful fallback döndür.

## Geliştirme Notları

- Varsayılan tema koyu moddur; Tailwind ile kolayca özelleştirilebilir.
- `settingsStore.ts` katmanında `setField` ve `reset` fonksiyonlarıyla tüm sunum katmanı ayrıştırılmıştır.
- Yeni piyasalar veya göstergeler eklemek için `src/types/settings.ts` dosyasındaki union tipleri genişletin ve bileşenlerdeki haritalamaları güncelleyin.

## Test ve Kalite

- Lint ve build aşamaları CI/CD'ye entegre edilebilir.
- Tür güvenliği `strict` TypeScript ayarları ile sağlanır.
- Tailwind JIT sayesinde yalnızca kullanılan stiller build'e dahil edilir.

## Lisans

Bu proje FinPilot iç kullanımı için hazırlanmıştır.
