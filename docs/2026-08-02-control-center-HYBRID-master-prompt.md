# FinPilot Control Center — HYBRID Master Prompt (tasarım)

Tarih: 2026-08-02 · Sürüm: 1.0 (v0.4 planıyla hizalı)
Kaynak: `docs/2026-08-02-ortak-beyin-handoff-buzz-claude-yol-plani.md` (v0.4) + `.finpilot/` veri modeli
Durum: Level A tasarım çıktısı (yeni izole doküman). Uygulama Level B/C kapılarına tabidir.

Bu, önceki üç ayrı promptun yerini alan **tek** hibrit master prompttur. İçine şu düzeltmeler işlendi: (1) Level C'de onay butonu YOK, (2) eski Buzz/adapter dili kaldırıldı, (3) tek-route yerine 5 route + route-taşınabilir bileşenler, (4) canonical kimlikler (`claude-cowork` vb.), (5) ajanları yarıştırmayan göstergeler, (6) tutarlı Türkçe yüzey dili.

Kullanım: Aşağıdaki bloğu bir UI üretim aracına (v0.dev, Lovable, Bolt, Figma Make veya Claude/GPT) olduğu gibi yapıştır.

```
Rol: Kıdemli bir ürün tasarımcısı ve front-end mühendisisin. Tek bir operatör için,
sakin ama karakterli, çok-sayfalı bir yönetim paneli (Control Center) tasarla ve üret.

# ÜRÜN BAĞLAMI
FinPilot Control Center — bir finansal tarama/sinyal ürününün İÇ operasyon kokpiti.
AI ajanları (GitHub Copilot, Claude Code, Claude Cowork) ve ürün ajanlarının işlerini
tek yerden izlemek ve (ileride) kontrollü onaylamak için. KRİTİK ilkeler:
- Otorite REPO'dadır. Bu panel bir GÖRÜNTÜLEME (read model) + kontrollü onay yüzeyidir;
  veri kaynağı değildir. Her kayıt repodaki bir Work Item/Handoff/Evidence'ı yansıtır.
- v1 SALT-OKUNUR. Yazma/aksiyon butonları görünür ama pasif ve "v2" rozetli.
- Panelde publish/deploy/broker/emir/secret KONTROLÜ YOKTUR (insanda kalır).
- Al/sat/hedef-fiyat gibi finansal tavsiye dili HİÇBİR yerde geçmez.
- Secret/PII asla gösterilmez.

# KULLANICI
Tek kişilik kurucu-operatör (Meriç). Açılışta cevabını istediği tek soru:
"Şimdi benden ne bekleniyor?" Gürültü istemez; derinliği ister ama gerektiğinde.

# BİLGİ MİMARİSİ — 5 ROUTE (her biri farklı yoğunlukta)
Ortak kabuk: solda kömür (charcoal) tonunda dar navigasyon (Bugün, İşler, Onaylar,
Ajanlar, Sistem), üstte ince bir durum şeridi (sistem sağlığı ışığı + son eşitleme
saati + operatör adı). İçerik alanı sakin/aydınlık.

1) /ops  →  "Bugün"  (dil: SAKİN/ODAK)
   Açılış ekranı. Yukarıdan aşağıya: kısa günün özeti (X onay bekliyor, Y blokaj);
   "Onayını bekleyenler" (öne çıkan); "Devam edenler"; "Takılanlar"; "Ajan durumu"
   mini listesi. Progressive disclosure: özet önde, detay tıklayınca sağ çekmecede.

2) /ops/approvals  →  "Onaylar"  (dil: SAKİN/ODAK, aynı anda tek karar)
   Level B/C review bekleyen işler. Her kart: başlık, WI-ID, Level rozeti, kanıt özeti
   (testler, diagnostics, commit), tek net sonraki aksiyon. Sağ çekmecede handoff
   zinciri + evidence. **Level ayrımı burada zorunlu (aşağıya bak).**

3) /ops/work  →  "İşler"  (dil: AKIŞ/BOARD)
   Segmented control ile iki görünüm:
   a) Durum panosu (kanban): sütunlar = Öneri → Hazır → Devam ediyor → Takıldı →
      İncelemede → Tamam. Kartlar: WI-ID, başlık, owner avatarı, Level, öncelik
      (P0..P3), kanıt rozetleri, yaş, blokaj işareti.
   b) Ajan şeritleri (swimlanes): satır = aktör; handoff'lar şeritler arası ince ok.
   NOT: sürükle-bırakla durum değiştirme YOK (güvenlik). Geçiş yalnız karttaki açık
   buton + v1'de pasif "v2".

4) /ops/agents  →  "Ajanlar"  (dil: sadeleştirilmiş swimlane)
   Her aktör için durum kartı ve aktif/sıradaki işleri. Göstergeler ajanları
   YARIŞTIRMAZ (aşağıya bak).

5) /ops/system  →  "Sistem"  (dil: YOĞUN/OPERASYON — Mission Control)
   Daha yoğun sağlık görünümü: CI, scanner (metadata-only durum), distribution,
   read-model tazeliği, veri akışı. Durum ışıkları + son başarılı eşitleme zamanları.
   Burada yoğunluk serbest; ama yine yalnız durum/gözlem, kontrol değil.

# VERİ MODELİ (canonical — gerçekçi Türkçe mock üret)
WorkItem { id:"WI-20260802-001", title, status: proposed|ready|in_progress|blocked|
  review|done|cancelled, owner, requested_by:"meric", level:"A"|"B"|"C",
  priority:"P0".."P3", age, blocked_by[], evidence_summary:{tests,diagnostics,commit},
  next_action, approval_state:"none"|"pending"|"approved" }
Handoff { id:"HO-...", work_item_id, from_actor, to_actor, state: ready|accepted|
  rejected|superseded, summary }
Evidence { id:"EV-...", work_item_id, kind: test|commit|diff|report|runtime,
  outcome: passed|failed|partial|plan-only|unknown, locator }
Aktörler (teknik ID → görünen ad):
  claude-code → "Claude Code" · vscode-copilot → "GitHub Copilot" ·
  claude-cowork → "Claude Cowork" · finpilot-agent:<name> → "Ürün Ajanı: <name>" ·
  meric → "Meriç" (operatör)

# LEVEL A/B/C DAVRANIŞI (aksiyon görünürlüğü)
- Level A: otonom. Kartta durum + kanıt; özel onay gerekmez.
- Level B: "İncele + Onayla" akışı. v1'de butonlar PASİF "v2"; kanıt özeti + "Onay
  bekliyor" şeridi görünür.
- Level C: İNSAN ZORUNLU. Kartta "Onayla/Uygula" BUTONU GÖSTERİLMEZ. Yalnız:
  "İnsan kararı gerekli" etiketi, "Kanıtı incele" ve "VS Code'da aç". Panel Level C'yi
  asla uygulanabilir bir aksiyon gibi sunmaz.

# AJAN GÖSTERGELERİ (yarıştırma YOK)
Kod ajanları (Claude Code, Copilot) ve araştırma ajanı (Claude Cowork) AYNI metrikle
kıyaslanmaz. Ham "throughput/test sayısı" ile sıralama YAPMA. Göster:
- Ortak: durum (çevrimiçi|boşta|çalışıyor|takıldı|incelemede), aktif iş, blokaj süresi,
  handoff kabul süresi, kanıt tamlığı, son başarılı çıktı.
- Claude Cowork'e ÖZEL araştırma göstergeleri: toplanan kaynak sayısı, incelenen
  doküman/korpus, üretilen plan/kanıt paketi, açık soru sayısı. (Test sayısı DEĞİL.)

# DURUMLAR (eski Buzz/adapter dili KULLANMA)
- Boş: "Bugün seni bekleyen bir şey yok" (nazik).
- Yükleniyor: skeleton.
- Bayat/erişilemez read model: "Read model güncel değil — son başarılı eşitleme 14:32"
  veya "Control API erişilemiyor". (Sessiz, panik yok.)

# GÖRSEL DİL
- Açık nötr ana zemin; sol navigasyon kömür (charcoal) tonu.
- Sistem sağlığı için soğuk yeşil; amber YALNIZ dikkat gereken durumlar; kırmızı YALNIZ
  gerçek hata / policy ihlali.
- Kart yerine mümkünse ayraçlı (divider) kompakt listeler; masaüstünde satır, mobilde
  kart özeti.
- Maksimum 8px köşe yarıçapı. Gölge minimal.
- ID, commit hash ve süreler monospace. Başlıklarda sakin ama ayırt edici bir yazı tipi.
- Mikro-etkileşim: yumuşak açılır detay çekmecesi; abartısız geçişler; kritik olan az ve net.

# TÜRKÇE YÜZEY DİLİ (İngilizce event adları yalnız ayrıntı katmanında)
Bugün · Onaylar · İşler · Ajanlar · Sistem Sağlığı · Devam edenler · Takılanlar ·
Onay bekliyor · İnsan kararı gerekli · Kanıtı incele · VS Code'da aç · Kanıt özeti.

# GÜVENLİK KISITLARI (tekrar — bağlayıcı)
v1 salt-okunur; tüm yazma/atama/onay butonları pasif "v2". Level C'de onay/uygula
butonu YOK. Publish/deploy/broker/emir/secret kontrolü YOK. Finansal tavsiye dili YOK.
Secret/PII gösterme. Panel repo gerçeğini geçersiz kılamaz.

# TEKNİK HEDEF
Next.js (App Router) + TypeScript + Tailwind (+ shadcn/ui opsiyonel). Beş route:
/ops, /ops/approvals, /ops/work, /ops/agents, /ops/system. Bileşenler route-taşınabilir
(paylaşılan kabuk + sayfa-özel içerik). Masaüstü öncelikli, responsive (mobilde kartlar).
Erişilebilir (kontrast, klavye, odak halkaları).

# TESLİM
Beş route için yüksek sadakatli, çalışan mockup + temiz, bileşenlere ayrılmış kod.
Gerçekçi Türkçe örnek veriyle doldur: en az 10 Work Item (karışık status/level/priority),
4 aktör (Claude Code, GitHub Copilot, Claude Cowork, bir ürün ajanı), birkaç handoff ve
evidence. En az bir Level C işi göster (onay butonsuz) ve bir "read model güncel değil"
durumu göster.
```

---

## Notlar
- Bu prompt, önceki 3 promptu (`...master-promptlari.md`) birleştirip düzeltir; o dosya referans/karşılaştırma için kalabilir, ama üretim için BUNU kullan.
- Ana kabuk **Sakin/Odak**; **Akış/Board** yalnız `/ops/work` ve sadeleştirilmiş haliyle `/ops/agents`; **Yoğun/Operasyon** yalnız `/ops/system`. Böylece "şimdi benden ne bekleniyor?" önde kalır, akış ve sistem derinliği kaybolmaz.
- Uygulama sırası: önce `/ops` (Bugün) + `/ops/approvals` iskeleti (en yüksek değer), sonra `/ops/work`, en son `/ops/system`.
