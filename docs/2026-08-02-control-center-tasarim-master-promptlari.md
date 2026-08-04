# FinPilot Control Center — Tasarım için 3 Master Prompt

Tarih: 2026-08-02 · Kaynak plan: `docs/2026-08-02-ortak-beyin-handoff-buzz-claude-yol-plani.md` (v0.4)
Kullanım: Aşağıdaki üç prompttan birini bir UI üretim aracına (v0.dev, Lovable, Bolt, Figma Make veya Claude/GPT) **olduğu gibi** yapıştır. Üçü birbirinden farklı tasarım yönü verir; karşılaştırıp seçersin. Hepsi aynı ürün bağlamına ve `.finpilot/` veri modeline dayanır; yalnız **görsel dil ve yerleşim felsefesi** farklıdır.

> Ortak güvenlik kuralı (üç prompt da içerir): Bu ekran yalnız **operatör Meriç**e açık iç yönetim panelidir. Al/sat/hedef-fiyat gibi finansal tavsiye dili **hiçbir yerde** geçmez. Panelde publish/deploy/broker/emir/secret **kontrolü yoktur**; bunlar insanda kalır. v1 **salt-okunur**dur (aksiyon butonları görünür ama devre dışı/"v2" etiketli). Secret/PII asla gösterilmez.

---

## MASTER PROMPT 1 — "Mission Control" (yoğun operatör kokpiti)

```
Rol: Kıdemli bir ürün tasarımcısı ve front-end mühendisisin. Tek bir operatör için
yüksek yoğunluklu bir "mission control" yönetim paneli tasarla ve üret.

Ürün: FinPilot Control Center — bir finansal tarama/sinyal ürününün İÇ operasyon
kokpiti (/ops yüzeyi). Amaç: yapay zekâ ajanlarının (GitHub Copilot, Claude Code,
Claude Cowork) ve ürün ajanlarının çalıştığı işleri tek yerden izlemek. Otorite
repo'dadır; bu panel bir GÖRÜNTÜLEME + kontrollü onay yüzeyidir, veri kaynağı değil.

Kullanıcı: Tek kişilik kurucu-operatör. Her şeyi bir bakışta, hızlı görmek ister.

Üretilecek ekran: Tek sayfa, 6 bloklu bir kokpit (/ops).
1) Today — bugün açılan/biten/bloklanan/review bekleyen iş sayıları + mini akış.
2) Approval Queue — Level B/C review bekleyen işler; risk bayrağı + kanıt özeti.
3) Agent Board — Copilot/Claude Code/Cowork/ürün ajanı: durum, aktif iş, son heartbeat, 7 günlük throughput.
4) Blockers — blokaj süresi, neden, beklenen aktör.
5) System Health — CI, scanner, distribution, adapter, stale-data (metadata-only, sadece durum ışıkları).
6) Reports — günlük özet + haftalık metrik kısayolları.
Sağdan açılan bir "Work Item detay" çekmecesi: başlık, durum, Level, owner, yaş,
handoff zinciri (from→to), evidence listesi (test/commit/diff), next_action.

Veri modeli (gerçekçi Türkçe mock üret):
- WorkItem { id: "WI-20260802-001", title, status: proposed|ready|in_progress|blocked|review|done, owner: cowork|claude-code|vscode-copilot|meric, level: A|B|C, priority: P0..P3, age, blocked_by[], evidence_summary: {tests, diagnostics, commit}, next_action, approval_state: none|pending|approved }
- Agent { actor, state: online|idle|working|blocked|review, active_work_item, last_heartbeat, done_7d, blocked_7d }
- Evidence { kind: test|commit|diff|report, outcome: passed|failed|partial, locator }

Görsel yön (BU prompt'a özgü):
- Koyu tema, "observability/terminal" hissi (Linear × Datadog × işlem terminali).
- Yüksek bilgi yoğunluğu, kompakt satırlar, küçük ama net tipografi.
- ID'ler, metrikler ve durum kodları için monospace vurgu.
- Renk yalnız anlam taşısın: durum ışıkları (yeşil/sarı/kırmızı), Level rozetleri, P0 vurgusu. Aksi halde nötr gri paleti.
- Üstte ince bir global durum çubuğu (System Health + saat + operatör). Solda dar ikon-nav.
- Mikro-etkileşim: hover'da satır aç, canlı "son güncelleme" damgası. Abartısız.

Durumlar: boş durum, yükleniyor (skeleton), hata, "Buzz/adapter bağlı değil" uyarısı.

Kısıtlar/güvenlik: Yukarıdaki ortak güvenlik kuralı geçerli. Aksiyon butonları
(approve/assign/priority) GÖRÜNÜR ama "v2 — read-only pilot" rozetiyle pasif.
Publish/deploy/broker/secret kontrolü YOK. Finansal tavsiye dili YOK.

Teknik hedef: Next.js (App Router) + TypeScript + Tailwind; istersen shadcn/ui.
Masaüstü öncelikli, responsive. Erişilebilir (kontrast, klavye). Tek route: /ops.

Teslim: Yüksek sadakatli, çalışan bir mockup + bileşenlere ayrılmış temiz kod.
Gerçekçi Türkçe örnek verilerle doldur.
```

---

## MASTER PROMPT 2 — "Calm Focus" (sakin, minimal, tek-akış)

```
Rol: Sadelik ve odak konusunda usta bir ürün tasarımcısısın. Tek operatör için,
bilişsel yükü en aza indiren sakin bir yönetim paneli tasarla ve üret.

Ürün: FinPilot Control Center (/ops) — AI ajanlarının (Copilot, Claude Code,
Cowork) ve ürün ajanlarının işlerini yöneten iç kokpit. Otorite repo'dadır; panel
görüntüleme + kontrollü onay yüzeyidir.

Kullanıcı: Tek kişilik kurucu-operatör. "Şu an benden ne bekleniyor?" sorusuna
saniyeler içinde cevap ister; gürültü istemez.

Tasarım felsefesi: Tek sütun, öncelik akışı. Progressive disclosure — özet önde,
detay tıklayınca açılır. Aynı anda tek karar. En üstte "Bugün seni bekleyen"
(onay kuyruğu) her şeyin önünde.

Üretilecek ekran (/ops), yukarıdan aşağıya:
- Başlık: "İyi çalışmalar, Meriç" + tek satır günün özeti (X onay bekliyor, Y blokaj).
- "Onayını bekleyenler" — Level B/C işlerin sade kartları: başlık, kanıt özeti
  (testler geçti/başarısız), tek net sonraki aksiyon. (Aksiyon v1'de pasif, "v2").
- "Devam edenler" — aktif işler, sahibi ajan avatarıyla, ilerleme hissi.
- "Takılanlar" — blokajlar, nazik bir uyarı tonuyla.
- "Ajanların durumu" — küçük, sakin bir liste (kim çalışıyor/boşta/takıldı).
- "Bugünün özeti" linki (rapora iner).

Veri modeli (gerçekçi Türkçe mock): [MASTER PROMPT 1'deki WorkItem/Agent/Evidence
şemasının aynısını kullan.]

Görsel yön (BU prompt'a özgü):
- Aydınlık tema, bol beyaz alan, geniş satır aralığı. Vercel/Notion sadeliği.
- Yumuşak nötr paleti + TEK sıcak vurgu rengi (yalnız "dikkat isteyen" için).
- Büyük, okunur tipografi; başlıklar sakin, gövde rahat.
- Kart temelli ama hafif; gölge yerine ince ayraçlar. Yuvarlak köşeler, nazik.
- Mikro-etkileşim: yumuşak açılır detay, hafif geçişler. Hiç titreşim/kırmızı bombardımanı yok — kritik olan az ve net.

Durumlar: "Bugün seni bekleyen bir şey yok 🎉" boş durumu; skeleton; hata; adapter yok uyarısı (sessiz).

Kısıtlar/güvenlik: Ortak güvenlik kuralı. v1 salt-okunur; aksiyonlar pasif/"v2".
Publish/broker/secret YOK. Finansal tavsiye dili YOK. Secret/PII gösterme.

Teknik hedef: Next.js (App Router) + TypeScript + Tailwind (+ shadcn/ui opsiyonel).
Masaüstü + tablet responsive. Erişilebilirlik önceliği. Tek route: /ops.

Teslim: Yüksek sadakatli, çalışan mockup + temiz bileşen kodu; gerçekçi Türkçe
örnek verilerle.
```

---

## MASTER PROMPT 3 — "Flow Board" (iş-akışı panosu + ajan şeritleri)

```
Rol: İş akışı ve kanban tarzı araçlar konusunda uzman bir ürün tasarımcısısın.
İşin bir aktörden diğerine akışını GÖRSELLEŞTİREN bir yönetim panosu tasarla ve üret.

Ürün: FinPilot Control Center (/ops) — AI ajanları (Copilot, Claude Code, Cowork)
ve ürün ajanları arasında işlerin devredildiği (handoff) iç kokpit. Otorite
repo'dadır; panel görüntüleme + kontrollü onay yüzeyidir.

Kullanıcı: Tek kişilik kurucu-operatör. İşin nerede olduğunu, kimin üstünde
olduğunu ve tıkanmaları bir board üzerinde görsel olarak görmek ister.

Üretilecek ekran (/ops): İki görünüm arası geçiş (segmented control):
A) DURUM PANOSU (kanban): Sütunlar = proposed → ready → in_progress → review → done.
   Her kart: WI-ID, başlık, owner avatarı, Level rozeti (A/B/C), priority (P0..P3),
   kanıt rozetleri (✓12 test, commit hash), yaş, blokaj işareti. review sütunundaki
   Level B/C kartlarında "onay bekliyor" şeridi.
B) AJAN ŞERİTLERİ (swimlanes): Satırlar = aktörler (Copilot, Claude Code, Cowork,
   ürün ajanı). Her şeritte aktörün aktif ve sıradaki işleri; şeridin başında ajan
   durum kartı (online/working/blocked, son heartbeat, 7g throughput). Handoff'lar
   şeritler arası ince oklarla gösterilir (from→to).
Üstte özet şeridi: Today sayıları + Approval Queue rozeti + System Health ışıkları.
Karta tıklayınca sağda detay: handoff zinciri (from→to→...), evidence listesi, next_action.

Veri modeli (gerçekçi Türkçe mock): [MASTER PROMPT 1'deki WorkItem/Agent/Evidence
şemasının aynısı; ayrıca Handoff { id, work_item_id, from_actor, to_actor, state:
ready|accepted|rejected|superseded, summary }.]

Görsel yön (BU prompt'a özgü):
- Board-öncelikli, görsel ve canlı ama düzenli. Trello/Linear board × hafif üretim-hattı estetiği.
- Nötr zemin + aktör başına yumuşak bir renk kodu (Copilot/Claude/Cowork ayırt edilsin).
- Kartlar okunur, rozetler küçük ve tutarlı. Sütun başlıkları sayaçlı.
- Handoff okları ince, dikkat dağıtmadan akışı anlatır.
- ÖNEMLİ: sürükle-bırak ile durum değiştirme YOK (güvenlik). Durum geçişi yalnız
  karttaki açık butonla ve v1'de pasif/"v2" rozetiyle. Board görsel, aksiyon kontrollü.

Durumlar: boş sütun, skeleton, hata, adapter yok uyarısı.

Kısıtlar/güvenlik: Ortak güvenlik kuralı. v1 salt-okunur; geçiş/atama butonları
pasif "v2". Publish/broker/secret YOK. Finansal tavsiye dili YOK. Secret/PII yok.

Teknik hedef: Next.js (App Router) + TypeScript + Tailwind (+ shadcn/ui opsiyonel).
Masaüstü öncelikli (yatay board), responsive olarak tablet'te dikey yığılma.
Erişilebilir. Tek route: /ops.

Teslim: Yüksek sadakatli, çalışan mockup + bileşen kodu; gerçekçi Türkçe örnek
verilerle (en az 8-10 Work Item, 4 ajan, birkaç handoff).
```

---

## Nasıl seçersin
- **Prompt 1 (Mission Control):** Her şeyi tek bakışta, hız ve yoğunluk istiyorsan.
- **Prompt 2 (Calm Focus):** "Şu an ne yapmalıyım"a odak, düşük gürültü istiyorsan.
- **Prompt 3 (Flow Board):** İşin ajanlar arası akışını ve devirleri görselleştirmek istiyorsan.

İpucu: Üçünü de ayrı ayrı üretip ekranları yan yana koy; muhtemelen **Calm Focus'un onay-kuyruğu** + **Flow Board'un ajan şeritleri** kombinasyonu tek operatör için en verimlisi olur. İstersen bu ikisini birleştiren 4. bir "hibrit" master prompt da yazarım.
