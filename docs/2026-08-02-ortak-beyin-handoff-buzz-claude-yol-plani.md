# FinPilot Control Center, Ortak Beyin ve Handoff Katmani

Surum: 0.4
Tarih: 2026-08-02
Durum: DRAFT - Level B mimari onerisi, Meric onayi bekliyor
Katman: Engineering / Operations / Agent Coordination
Hedef: FinPilot web uygulamasi icinde Meric'e ozel bir Control Center kurmak,
VS Code'u ana muhendislik calisma ortami, repoyu kalici ortak beyin yaparak
GitHub Copilot, Claude Code, Claude Cowork ve FinPilot urun ajanlarini ayni gorev
ve kanit zincirinde birlestirmek.

Revizyon 0.2: VS Code ana insan calisma ortami ve kontrol yuzeyi olarak mimariye,
fazlara, backlog'a, testlere ve operasyon ritueline acikca eklendi.

Revizyon 0.3: Yonetim ve gorunurluk VS Code'dan ayrildi. Buzz, Meric Control
Cockpit; VS Code, Engineering Workbench; repo, Shared Brain / Source of Truth
olarak konumlandirildi. Cockpit ekranlari, raporlar, adapter bilesenleri, sinirli
geri yazma ve uygulama sirasi ayrintilandirildi.

Revizyon 0.4: Buzz ana kontrol kokpiti olmaktan cikarildi. Mevcut Next.js/FastAPI
altyapisinda, yalniz yetkili operatorlere acik FinPilot-native Control Center
onerildi. Claude Cowork ayri bir arastirma/operasyon yurutucusu olarak role,
handoff akislarina ve backlog'a eklendi. Basit, akici ve anlasilir web bilgi
mimarisi ile kademeli uygulama modeli tanimlandi; Buzz opsiyonel bildirim adaptoru
olarak birakildi.

> Bu belge bir uygulama plani ve karar taslagidir. Mevcut scanner, distribution,
> publish, risk veya emir davranisini degistirmez. Yeni `/ops` yuzeyi, Control API,
> veri modeli ve workflow eklenmesi ayri Level B uygulama kapilaridir.
> Publish/emir/secrets yetkisi Level C olarak insanda kalir.

---

## 1. Yonetici karari

Onerilen model uygulanabilir ve FinPilot'in mevcut kod tabanina Buzz merkezli
modelden daha iyi oturur. FinPilot-native web yuzeyi yonetim kokpiti; repo ortak
beyin ve nihai otorite olmalidir.

Teknik karar taslagi:

1. **Repo kalici ortak beyin ve tek dogrulanabilir gercektir.**
2. **FinPilot Control Center, Meric'in yonetim kokpitidir.** Gorev acma,
   onceliklendirme, sahiplik, ilerleme, blokaj, rapor ve sinirli onay intent'leri
   web uygulamasindaki ayri `/ops` yuzeyinde gorulur.
3. **VS Code, Engineering Workbench'tir.** Kod, terminal, Source Control, Problems,
   Test Explorer, teknik diff ve ayrintili review burada birlesir.
4. **GitHub Copilot ve Claude Code VS Code merkezli ayri yurutuculerdir.** Birbirinin
  sohbet hafizasina degil, ayni Work Item + Handoff + Evidence sozlesmesine dayanir.
5. **Work Item + Handoff + Evidence sozlesmesi arac-bagimsiz omurgadir.**
6. **Control Center kontrollu intent uretir; otorite kaydini dogrudan degistirmez.**
  Intent, operator kimligi ve policy kontrolunden sonra canonical CLI ile repo
  kaydina uygulanir ve audit edilir.
7. **Claude Cowork ayni bootstrap ve handoff sozlesmesini kullanan ayri bir
  arastirma/operasyon yurutucusudur.** Kaynak toplar, dokuman/korpus inceler,
  plan ve kanit paketi uretir; production kodunu veya finansal kurallari sessizce
  degistirmez.
8. **FinPilot urun ajanlari yalniz tanimli olaylari tuketir/uretir; gelistirme
   ajanlarindan gelen serbest metni dogrudan production aksiyonuna cevirmez.**
9. **Yayin, risk/esik, prod config, secret ve emir kapilari Meric'te ve mevcut
  ayri kapilarinda kalir.** Control Center bu aksiyonlari cagiramaz.

Bu ayrim Meric'e tek ve okunabilir bir yonetim yuzeyi verirken web uygulamasi
kesilse bile ortak hafizanin repoda kalmasini saglar. Control Center tekrar
baglandiginda repo gerceginden yeniden kurulur.

---

## 2. Mevcut durum - dogrulanan varliklar

FinPilot bu sistemin buyuk bolumune zaten sahip:

| Yuzey | Mevcut varlik | Rol |
| --- | --- | --- |
| Yonetim kokpiti | FinPilot web `web/src/app/ops/` | Henuz yok; mevcut Next.js dashboard, auth ve autonomy kaliplari yeniden kullanilabilir |
| Muhendislik ortami | VS Code workspace | Kod, terminal, SCM, test, hata ve teknik review; repo'da henuz `.vscode/tasks.json` veya `.code-workspace` yok |
| Ortak ajan bootstrap'i | `AGENTS.md`, `CLAUDE.md`, `_instructions/00-core.md` | Tum ajanlarin acilis ve escalation kurali |
| Otorite haritasi | `docs/INDEX.md` | Hangi sorunun hangi gercege bakacagini belirler |
| Kalici karar sicili | `docs/governance/decision-log.md` | Onayli/pending stratejik ve operasyonel kararlar |
| Urun ajan sozlesmesi | `agents/base.py` - `AgentContext`, `AgentResult` | Urun-ici ajan input/output kalibi |
| Urun ajan katalogu | `agents/registry.py` | Ajan sahipligi, katmani ve durum envanteri |
| Canonical urun pipeline'i | `core/pipeline.py` - `run_cycle()` | Scanner -> analiz -> risk -> alert akisi |
| Kisa omurlu ajan state'i | `core/agent_state.py` | Redis/in-memory, 1 saat TTL; kalici proje hafizasi degil |
| Canli aktivite akisi | `core/agent_events.py` | Redis listesi, en fazla 200 olay; Redis yoksa kaybolur |
| Sinyal yasam dongusu | `core/signal_events.py` | DB tabanli cycle/symbol/agent olay izi |
| Otonomi audit'i | `core/audit_log.py` | Append-only JSONL karar kaydi |
| Insan onay yuzeyi | `web/src/app/dashboard/autonomy/page.tsx` | Riskli urun-ici aksiyonlar icin approve/reject |
| Yayin kalite kapisi | `distribution/prepublish_gate.py`, `scripts/preview_publish.py` | Yayin oncesi butunluk, lint ve insan incelemesi |
| Operasyon sozlesmesi | `YONERGE.md` | Tek scan -> tek snapshot -> web + Telegram, secrets ve publish kurallari |

### Eksik olan

Mevcut sistemlerde su genel amacli sozlesme yok:

- Gelistirme veya arastirma isi icin tek `work_item_id`
- Kim baslatti, kim sahiplendi, kimden kime devredildi bilgisi
- Gorevin otorite katmani ve Level A/B/C sinifi
- Baslangic girdisi, beklenen cikti ve kapsam disi alanlar
- Degisen dosyalar/commit/test/rapor kanitlari
- Acik varsayimlar, blokajlar ve sonraki sahip
- FinPilot web'de aktif is, sahip, blokaj, kanit ve onaylari gosteren operator yuzeyi
- VS Code icinde aktif isi teknik baglamla gosteren ortak komut/task yuzeyi
- GitHub Copilot, Claude Code, Claude Cowork ve urun ajanlari arasinda makine-okunur
  devir paketi

Sonuc olarak araclar ayni repoyu gorse bile ayni **is durumunu** gormuyor.

### Dikkat edilmesi gereken mevcut tekrarlar

Yeni katman mevcut sistemleri birlestirmeye calisip dorduncu bir orkestrator
yaratmamalidir:

- `AgentContext`, `FinPilotState` ve API request/response semalari zaten farkli
  amaclarla state tasiyor.
- `agent_events`, `signal_events`, `audit_log` ve `decision-log.md` farkli yasam
  sureleri ve otorite seviyelerine sahip.
- Redis activity feed kalici proje hafizasi degildir.
- `signal_events` finansal sinyal yasam dongusudur; gelistirme gorev takip sistemi
  olarak genisletilmemelidir.
- `buzz_level` isimli sosyal metrik Buzz.xyz entegrasyonu degildir.

---

## 3. Hedef mimari

```text
                          MERIC - insan otoritesi
                                |
                      +-------------v--------------+
                      | FINPILOT CONTROL CENTER    |
                      | /ops - internal web        |
                      |----------------------------|
                      | Portfolio / active work    |
                      | Agents / blockers / SLA    |
                      | Evidence summaries         |
                      | Reports / approval intents |
                      +-------------+--------------+
                                |
                        signed, allowlisted intent
                                |
                      +-------------v--------------+
                      | Repo-native Shared Brain   |
                      |----------------------------|
                      | Work Item / Handoff        |
                      | Evidence / Decision refs   |
                      | Audit / outbox / inbox     |
                      +------+------+--------------+
                           |      |
                    read/write |      | metadata/events
                           |      |
                   +-----------v--+   +------------------------+
                   | VS Code      |                            |
                   | Engineering  |                      +-----v------+
                   | Workbench    |                      | Claude     |
                   |--------------|                      | Cowork     |
                   | Copilot      |                      +------------+
                   | Claude Code  |                            |
                   | SCM/Tests    |                  +---------v--------+
                   +------+-------+                  | FinPilot product |
                        |                          | agents/pipeline   |
                        +--------------------------+---------+--------+
                                                |
                                          existing human gate
                                                |
                                         Telegram / web / deploy
```

Control Center yonetim gorunumudur; VS Code teknik calisma gorunumudur. Hicbiri
tek basina verinin veya kararin otoritesi degildir. Browser ya da editor gecmisi
kaybolsa bile aktif is `.finpilot/` kayitlarindan yeniden kurulur.

### Otorite sirasi

1. `_instructions/00-core.md` ve Risk & Compliance
2. `docs/INDEX.md` ile bulunan alan otoritesi
3. `docs/governance/decision-log.md` onayli kararlar
4. Aktif Work Item ve son Handoff
5. Test/commit/rapor kanitlari
6. Control Center gorunumu/intent'i, VS Code/Claude Cowork sohbet ozeti veya ajan hafizasi

Control Center'daki bir kart repo gercegini gecersiz kilamaz. Bir operator intent'i
karar olacaksa `decision_ref` ile repodaki karar kaydina baglanir.

---

## 4. Ortak sozlesmeler

### 4.1 Work Item - isin kimligi

Her anlamli is bir kere olusturulur ve butun araclarda ayni ID ile tasinir.

Onerilen v1 alani:

```yaml
schema_version: 1
work_item_id: WI-20260802-001
title: "Ortak handoff protokolunu kur"
status: proposed          # proposed|ready|in_progress|blocked|review|done|cancelled
owner: vscode-copilot     # meric|vscode-copilot|claude-code|claude-cowork|finpilot-agent:<name>
work_surface: vscode      # ops-web|vscode|claude-cowork|finpilot-runtime
requested_by: meric
authority_layer: engineering
decision_level: B         # A|B|C
authority_refs:
  - AGENTS.md
  - _instructions/00-core.md
  - YONERGE.md
decision_refs: []
scope:
  include:
    - core/handoff/**
    - tests/handoff/**
  exclude:
    - scanner scoring
    - distribution publish
    - execution/broker
acceptance_criteria:
  - "Ayni paket VS Code Copilot, Claude Code ve Claude Cowork tarafindan okunabiliyor"
  - "Level B is onaysiz done olamiyor"
risk_flags:
  - external_service
  - new_data_model
created_at: "2026-08-02T00:00:00Z"
updated_at: "2026-08-02T00:00:00Z"
```

### 4.2 Handoff - devir paketi

Handoff yeni gorev yaratmaz; mevcut Work Item'in kontrolunu veya bilgi paketini
bir sonraki aktore devreder.

```yaml
schema_version: 1
handoff_id: HO-20260802-001
work_item_id: WI-20260802-001
from_actor: claude-cowork
to_actor: claude-code
state: ready             # ready|accepted|rejected|superseded
summary: "Repo envanteri tamamlandi; uygulama semasi hazir."
facts:
  - claim: "Genel amacli handoff semasi yok"
    evidence_ref: "search:handoff-20260802"
assumptions:
  - "Control Center yalniz internal operator yuzeyi olacak"
open_questions:
  - "Kalici store git dosyasi mi SQLite mi olacak?"
artifacts:
  - path: docs/2026-08-02-ortak-beyin-handoff-buzz-claude-yol-plani.md
validation:
  commands: []
  result: "plan-only"
next_action: "v1 JSON Schema ve validator icin Level B onayi al"
blocked_by: []
created_at: "2026-08-02T00:00:00Z"
```

### 4.3 Evidence - kanit indeksi

Buyuk log veya sohbetler Work Item'a gomulmez. Kanitlar referanslanir:

```yaml
- evidence_id: EV-20260802-001
  work_item_id: WI-20260802-001
  kind: test              # test|commit|diff|report|runtime|external_source
  locator: "pytest tests/handoff -q"
  outcome: passed
  produced_by: claude-code
  timestamp: "2026-08-02T00:00:00Z"
```

### 4.4 Durum gecisleri

```text
proposed -> ready -> in_progress -> review -> done
                       |              |
                       v              v
                    blocked       in_progress
```

Kurallar:

- Level A: ajan `done` yapabilir; kanit zorunlu.
- Level B: ajan `review`'a getirir; Meric onayi olmadan `done` olmaz.
- Level C: ajan sadece `proposed/review` durumuna kadar ilerler; uygulama ve nihai
  onay insan tarafindan yapilir.
- Bir aktor devri kabul etmeden `owner` degismez.
- Son Handoff oncekini silmez; `superseded` olarak isaretler.
- Sohbet ozeti kanit degil; kanit referanslarinin indeksi olabilir.

---

## 5. Calisma yuzeyleri, aktorler ve yetki matrisi

| Yuzey/Aktor | Okur | Yazar | Yapamaz |
| --- | --- | --- | --- |
| FinPilot Control Center | Work Item portfoyu, ajan durumu, blokaj, kanit ozeti, rapor, onay intent'i | Allowlist'li create/assign/priority/approve/reject/request_changes intent'i | Repo otoritesini, publish'i veya broker'i dogrudan degistirme |
| VS Code Workbench | Workspace, Work Item, diff, Problems, testler, terminal | Insan veya yetkili ajan araciligiyla repo dosyalari | Yonetim gercegini kendi sohbet state'inde tutma |
| Meric | Control Center'da operasyon ozeti; VS Code'da teknik ayrinti; repoda otorite kaydi | Onay/red, oncelik, sahip atama, publish karari | - |
| GitHub Copilot (VS Code) | Kod, test, docs, Work Item, editor baglami | Patch, test kaniti, handoff, review | Emir, secret rotasyonu, onaysiz publish/merge |
| Claude Code | Kod, test, docs, Work Item | Patch, test kaniti, handoff, review | Emir, secret rotasyonu, onaysiz publish/merge |
| Claude Cowork | Dokuman, korpus, web/arastirma, plan ve operasyon dosyalari | Kaynakli rapor, kabul kriteri, handoff, decision taslagi, tutarlilik review'u | Production kodunu, risk/urun kuralini veya otorite belgesini onaysiz degistirme |
| FinPilot urun ajani | Kendine acik contract ve gerekli input | AgentResult, signal event, sinirli evidence | Serbest repo gorevi alma, governance karari verme |
| Ops projector/API | Repo kayitlari, metadata ve izinli ozet | Read model, allowlist'li intent, audit olayi | Repo disinda ikinci otorite yaratma, secret/ham veri tasima |
| CI | Commit ve test konfigurasyonu | Status/evidence olayi | Onay gerektiren karari otomatik onaylama |

### FinPilot Control Center'in rolu

Control Center, Meric'in gunluk yonetim ve gozlem yuzeyidir. Meric kod diff'ini
web ekraninda okumaya zorlanmaz; once karar icin gereken ozet ve kaniti gorur,
teknik ayrinti gerektiginde Work Item'daki VS Code/commit/evidence referansina iner.

Control Center'da yapilabilecekler, guvenli geri yazma fazi acildiktan sonra:

- Work Item acma ve oncelik (`P0..P3`) belirleme
- Copilot, Claude Code veya Claude Cowork'a sahiplik atama
- `blocked` is icin aciklama ve yeni sahip isteme
- Level B is icin `approve`, `reject`, `request_changes` intent'i verme
- Gunluk/haftalik raporu okuma ve ilgili Work Item thread'ine inme
- Incident'i acknowledge etme ve root-cause Work Item'i acma

Control Center'da yapilamayacaklar:

- Dosya icerigini veya decision-log'u dogrudan yazma
- Git merge/push, deploy veya publish calistirma
- Scanner skoru, risk esigi, entry/exit veya broker aksiyonu degistirme
- Secret, ham snapshot, kullanici PII veya broker bilgisini gorme/tasima

### VS Code'un ana muhendislik ortami olarak rolu

VS Code, teknik calismanin baslangic ve bitis noktasidir:

- Explorer/editor: otorite belgeleri, aktif Work Item ve kod birlikte acilir.
- Source Control: yalniz aktif Work Item'a ait diff review edilir; baska oturumun
  degisiklikleri stage edilmez.
- Problems ve Test Explorer: hata ve test evidence'i ayni yuzeyde gorulur.
- Terminal/Tasks: `handoff.py` komutlari ve odakli testler tekrarlanabilir task olarak
  calisir.
- GitHub Copilot Chat/Agent: VS Code icindeki birincil uygulama ve review yurutucusudur.
- Claude Code: VS Code terminali veya uygun entegrasyon icinden ikinci uygulama/review
  yurutucusu olarak ayni Work Item'i kullanir.
- Meric, Control Center'daki karar ozetinden teknik kanita inmesi gerektiginde Level B/C
  review'u diff, Problems, test sonucu ve Handoff paketiyle VS Code'da tamamlar.

Ilk fazda ozel VS Code extension yazilmaz. `.vscode/tasks.json` ile `handoff:list`,
`handoff:show-active`, `handoff:validate`, `test:focused` ve `evidence:check`
task'lari saglanir. Ozel Tree View/Status Bar ancak task tabanli pilot yetersiz
kalirsa ayri Level B olarak degerlendirilir.

### GitHub Copilot'un rolu

- VS Code'da aktif Work Item ve son accepted Handoff'u okur.
- Kod, test, dokuman ve review islerini mevcut repo talimatlariyla uygular.
- Problems/Test Explorer/terminal sonucunu evidence referansina cevirir.
- Level B/C isi `review` durumunda Meric'e birakir.
- Claude Code ile ayni dosyada eszamanli yazmaz; owner ve worktree kuralina uyar.

### Claude Code'un rolu

- Work Item'i kabul et
- Repo otoritelerini oku
- Branch/worktree uzerinde kodla
- Test ve diff kanitini Handoff'a yaz
- Repo-native event ile kisa, secrets icermeyen durum guncellemesi uret
- Level B/C isi `review` durumunda Meric'e devret

GitHub Copilot ve Claude Code'a ilk pilotta verilmeyecekler:

- Telegram token veya kanal yayin yetkisi
- Render/Vercel production credential
- Alpaca/broker credential veya emir cagrisi
- `main` dalina otomatik push/merge
- Scanner skor/risk/entry-exit kurallarini onaysiz degistirme

### Claude Cowork'un rolu

- Dis kaynak, web, dosya ve korpus arastirmasi yapar.
- Dokumanlar arasi otorite, celiski ve eksik kanit analizi yapar.
- Work Item icin kaynakli brief, kabul kriteri, varsayim ve kapsam disi alan uretir.
- Copilot veya Claude Code'a uygulanabilir `research -> implementation` Handoff'u verir.
- Uzun sureli dokuman, rapor, veri tasnifi ve operasyon hazirligi islerini yurutur.
- Uygulama sonrasi rapor, karar ve dokuman tutarliligini review eder.
- Her bulguda kaynak locator'i ve guven seviyesini evidence olarak kaydeder.

Claude Cowork production kodu icin varsayilan yazar degildir. Kod degisikligi
gereken bir bulgu urettiginde isi Copilot veya Claude Code'a devreder. Governance,
risk, publish veya finansal urun kurali iceren ciktiyi uygulamaz; `review` durumunda
Meric'e birakir.

Claude Cowork, GitHub Copilot ve Claude Code birbirinin serbest sohbet gecmisini
bilmek zorunda degildir; hepsi son kabul edilmis Work Item + Handoff + Evidence
paketini okur. Meric operasyon ozetini Control Center'da, teknik kaniti VS Code'da
denetler.

### Urun-ici ajanlarin rolu

Urun ajanlari gelistirme ajanlarindan ayrilmalidir:

- `AgentContext/AgentResult` korunur.
- Work Item yalniz izinli, makine-okunur bir `product_input_ref` uretir.
- Urun ajani sonucu tekrar evidence/operational event olarak disari verir.
- Serbest metin arastirma sonucu scanner skoruna veya publish'e dogrudan girmez.
- Finansal sonuc daima mevcut scanner/distribution contract ve insan kapisindan
  gecer.

---

## 6. Repo-native ortak beyin dosya yapisi

Ilk uygulama icin onerilen minimal yapi:

```text
.finpilot/
  work-items/
    WI-20260802-001.yaml
  handoffs/
    HO-20260802-001.yaml
  evidence/
    WI-20260802-001.yaml
  schemas/
    work-item.schema.json
    handoff.schema.json
    evidence.schema.json
  README.md

scripts/
  handoff.py              # validate/list/create/accept/complete; stdlib CLI

.vscode/
  tasks.json              # handoff, validation ve focused-test komutlari
  extensions.json         # yalniz gerekli/onerilen entegrasyonlar

tests/
  test_handoff_contract.py
  test_handoff_transitions.py
  test_handoff_redaction.py
```

### Neden once dosya + JSON Schema?

- Git diff ve review dogal olarak calisir.
- VS Code, GitHub Copilot, Claude Code ve Claude Cowork ek servis olmadan okuyabilir.
- Control Center gecici olarak kapali olsa da sistem kullanilir.
- Gecisler gorunur ve geri alinabilir.
- Yeni DB/migration/daemon gerektirmez.
- Ilk pilotta olcek dusuktur.

SQLite veya uzak event store ancak su olculmus esikler asilirsa degerlendirilir:

- Aktif Work Item sayisi >100
- Ayni anda >3 yazar
- Dosya merge catismasi haftada >2
- Query/filtre suresi operasyonu aksatiyor
- Web projector ile repo arasinda performans veya eszamanli yazma sorunu kanitlandi

Bu esiklerden once DB kurmak gereksiz ikinci bir gercek kaynagi yaratir.

### Git politikasi

- Work Item ve Handoff kucuk, secrets icermeyen, commit'li kayitlardir.
- Buyuk runtime loglari, model prompt dump'lari ve ham veri commit edilmez.
- Her uygulama commit'i Work Item ID tasir: `feat(handoff): ... [WI-...]`.
- Handoff commit'ten once veya ayni branch'te olusur; `main`'e otomatik merge yoktur.
- Concurrent ajanlar ayni worktree'de calismaz; ayri branch/worktree kullanir.

---

## 7. FinPilot-native web Control Center tasarimi

### 7.1 Konumlandirma

Control Center:

- Meric'in tek operasyonel giris noktasi
- yalniz operator/admin kimligine acik ayri `/ops` web alani
- Work Item, ajan, blokaj, SLA, Git/CI ve urun operasyon projeksiyonu
- form/action tabanli, policy-kontrollu intent'ler
- aranabilir operasyon ve rapor gecmisi

Control Center degildir:

- FinPilot otorite dokumani
- scanner state store
- karar sicilinin yerine gecen kayit
- secret manager
- publish veya broker kontrol duzlemi
- musteri dashboard'una eklenen bir admin karti

Mevcut `web/src/app/dashboard/autonomy/page.tsx` onay/audit kalibi,
`web/src/lib/auth.tsx` rol bilgisi ve `api/routers/closed_loop.py` admin endpoint
kalibi yeniden kullanilabilir. Buna ragmen `/ops`, musteriye acik `/dashboard`
navigasyonundan ve layout'undan ayrilmalidir. Bu ayrim hem anlasilabilirligi hem
de yanlis yetkilendirme riskini azaltir.

### 7.2 Web bilgi mimarisi

Ana navigasyon yalniz bes basliktan olusur:

| Route | Ekran adi | Tek cevapladigi soru |
| --- | --- | --- |
| `/ops` | Bugun | Su anda ilgilenmem gereken nedir? |
| `/ops/work` | Isler | Hangi is nerede, kimde ve neden bekliyor? |
| `/ops/agents` | Ajanlar | Copilot, Claude Code, Claude Cowork ve urun ajanlari ne yapiyor? |
| `/ops/approvals` | Onaylar | Benden hangi karar bekleniyor ve kaniti yeterli mi? |
| `/ops/system` | Sistem | FinPilot servisleri, CI ve veri akisi saglikli mi? |

Raporlar ayri bir ana menu olmaz; `Bugun` ekranindaki rapor bolumunden ve filtreli
detaylardan acilir. Ayarlar profil menusunde kalir. Böylece ana navigasyon buyumez.

#### Bugun ekrani

Ilk ekran alti bilgi blogu gosterir:

| Blok | Gosterilen | Kaynak | Meric aksiyonu |
| --- | --- | --- | --- |
| Bugun | Bugun acilan, biten, bloklanan, inceleme bekleyen isler | Work Item projection | Is detayina git |
| Onaylar | Level B/C incelemesi bekleyenler, risk bayragi, kanit ozeti | Work Item + governance policy | Incele |
| Ajanlar | Copilot/Claude Code/Claude Cowork/urun ajani: durum, aktif is, son heartbeat | Handoff + runtime event | Sahip degistir veya incele |
| Blokajlar | Blokaj suresi, nedeni, beklenen insan/ajan | Work Item | Goruldu olarak isaretle veya ata |
| Sistem Sagligi | CI, scanner, distribution, adapter, stale-data durumu | Allowlist'li operasyon event'i | Olay kaydi ac |
| Raporlar | Gunluk ozet, haftalik akis/kalite ve bypass denemeleri | Report generator | Detaya in |

Desktop'ta Approval Queue ve Blockers ilk viewport'ta gorunur. Mobilde sira:
kritik sistem uyarisi, bekleyen onay, blokaj, aktif is, ajanlar, raporlar. Yatay
scroll gerektiren genis tablo kullanilmaz; mobilde satirlar ozet kartlara doner.

#### Is detay cekmecesi

Liste satirina tiklandiginda once sag detay cekmecesi acilir; kullanici sayfa
baglamini kaybetmez. Cekmece yalniz karar icin gereken ozeti tasir:

```yaml
work_item_id: WI-20260802-001
title: "Ortak handoff protokolunu kur"
status: in_progress
priority: P1
owner: vscode-copilot
decision_level: B
age: 1d 4h
blocked_by: []
last_update: "Schema validator tamamlandi"
evidence_summary:
  tests: "12 passed"
  diagnostics: "0 error"
  commit: "abc1234"
next_action: "Meric review"
approval_state: pending
repo_ref: ".finpilot/work-items/WI-20260802-001.yaml"
```

Tam diff ve uzun log web ekranina kopyalanmaz. Cekmece ozet, degisen dosyalar,
test sonucu ve locator tasir; teknik ayrinti repo/CI/VS Code'da kalir. `VS Code'da
Ac` destegi guvenilir bicimde kurulamiyorsa buton locator'i kopyalar; desteklenmeyen
browser otomasyonu yapilmaz.

#### Ajan durum karti

Her ajan icin gorunur alanlar:

- `actor_id`, rol ve izin profili
- `online|idle|working|blocked|review` durumu
- aktif `work_item_id` ve sahiplik baslangic zamani
- son heartbeat ve son kanit
- son 7 gunde tamamlanan/bloklanan is sayisi
- ortalama handoff ve review suresi
- izin/bypass ihlali veya policy rejection sayisi

Heartbeat yoksa ajan otomatik `offline/stale` gorunur; Work Item baska ajana
sessizce atanmaz, Meric'e reassignment onerisi cikar.

Claude Cowork karti arastirma yuzeyine uygun ek alanlar tasir: aktif kaynak sayisi,
son kaynakli brief, bekleyen research handoff ve guven seviyesi. Bu alanlar kod
ajanlarinin test/diagnostic metrikleriyle ayni performans puanina cevrilmez.

### 7.3 Arayuz ilkeleri ve temel akislar

Arayuzun hedefi daha fazla veri gostermek degil, Meric'in siradaki dogru aksiyonu
hizli anlamasidir:

1. **Ozet -> detay -> karar:** Ana ekran sonuc verir; ayrinti cekmecede; teknik
  kanit VS Code/CI'da acilir.
2. **Bir ekranda birincil tek aksiyon:** Onay kartinda `Incele`; detayda
  `Onayla`, `Degisiklik iste`, `Reddet`.
3. **Renk tek basina anlam tasimaz:** Durumlarda ikon + metin + renk birlikte.
4. **Insan dili:** `handoff.accepted` yerine `Claude Cowork arastirmayi devretti`.
  Ham event tipi ikincil teknik detayda kalir.
5. **Progressive disclosure:** ID, hash, payload ve audit ayrintisi varsayilan
  gorunumde saklidir; istendiginde acilir.
6. **Stabil boyutlar:** Kartlar, sayaclar ve filtreler dinamik icerikle ziplamaz.
7. **Az ve tutarli durum:** `Hazir`, `Calisiyor`, `Bloklu`, `Incelemede`, `Tamam`.
8. **Geri bildirim:** Her intent sonrasinda sonuc, audit ID ve yeni durum gorulur.
9. **Erisilebilirlik:** Klavye navigasyonu, gorunur focus, semantic heading,
  yeterli kontrast ve reduced-motion destegi zorunludur.
10. **Hata sakin ve acik:** `Islem basarisiz` yerine neden, kaydin korunup
   korunmadigi ve tekrar denenebilirlik belirtilir.

#### Akis A - Yeni arastirma isi

```text
Yeni Is
  -> amac + kabul kriteri + karar seviyesi
  -> owner: Claude Cowork
  -> Claude Cowork kaynakli brief ve evidence uretir
  -> research handoff: Copilot veya Claude Code
  -> Control Center Meric'e durum ve kanit ozeti gosterir
```

#### Akis B - Uygulama ve review

```text
Research handoff kabul edilir
  -> VS Code'da ayri branch/worktree
  -> kod + focused test + diagnostics
  -> implementation handoff
  -> Control Center Onaylar kuyrugu
  -> Meric: onayla / degisiklik iste / reddet
```

#### Akis C - Blokaj

```text
Ajan isi blocked yapar
  -> tek cumle neden + beklenen kisi/kanit
  -> Bugun ekraninda sure sayaci
  -> Meric acknowledge, owner degistir veya aciklama ekler
  -> her degisim audit edilir
```

### 7.4 Raporlama modeli

#### Gunluk ozet - her is gunu

- Dun tamamlananlar ve kanitlari
- Bugun devam edenler ve sahipleri
- Meric onayi bekleyenler
- 24 saati asan blokajlar
- CI/test/adapter hatalari
- Repo ile web read model arasinda durum uyusmazligi
- Ertesi gunun ilk uc onceligi

#### Haftalik ajan ve sistem raporu

| Metrik | Neden |
| --- | --- |
| Baslatilan/tamamlanan/iptal edilen Work Item | Akis hacmi |
| Lead time ve cycle time medyan/p90 | Teslim hizi |
| Handoff kabul suresi | Ajanlar arasi koordinasyon |
| Review'dan geri donen is orani | Kanit/kalite |
| Blocked time ve ana nedenler | Darbogaz |
| Test/CI gecis orani | Teknik kalite |
| Owner cakismasi ve dirty-worktree olayi | Calisma izolasyonu |
| Policy rejection ve approval bypass denemesi | Governance guvenligi |
| Projector/API ve reconciliation basari orani | Cockpit guvenilirligi |
| Claude Cowork kaynakli brief kabul/red orani | Arastirma handoff kalitesi |

Raporlar performans baskisi icin degil, sistem darbogazini bulmak icindir. Ajanlar
yalniz is sayisiyla siralanmaz; dusuk riskli cok is ureten aktor, az ama zor bir
isi tamamlayan aktorden otomatik olarak "daha iyi" sayilmaz.

### 7.5 Uygulama bilesenleri

Ilk surumde yeni bir merkezi orkestrator yazilmaz. Bes kucuk bilesen kullanilir:

```text
.finpilot/*.yaml
  |
  v
scripts/control_projector.py  ->  Control API read model
  |                                  |
  |                                  v
  +----------------------------> web/src/app/ops

Operator form/action
  |
  v
POST /api/v1/control/intents -> .finpilot/inbox/*.json
  |                         |
  v                         v
 identity + nonce + policy -> scripts/handoff.py transition
              |
              v
          append-only audit/evidence
```

| Bilesen | Sorumluluk | Fail davranisi |
| --- | --- | --- |
| `handoff.py` | Canonical Work Item/Handoff gecisleri | Fail-closed |
| `control_projector.py` | Repo state'ini redakte web read modeline cevirme | Son basarili gorunumu koru, stale uyarisi ver |
| Control API | `/ops` icin liste, detay, ajan, onay, saglik ve rapor endpointleri | Yetkisiz istegi reddet; repo yazma yapma |
| Intent processor | Operator aksiyonunu canonical CLI gecisine cevirme | Dogrulanmayan intent'i quarantine et |
| Reconciler | Repo ile read model farkini bulma | Uyari olustur; web gorunumunu repo state'ine getir |
| Report generator | Gunluk/haftalik metrik ve ozet | Eksik veriyi `unknown` raporla |

Ilk surum mevcut Next.js + FastAPI + Python stdlib kaliplarini kullanir. Yeni bir
frontend framework, message broker veya operasyon veritabani eklenmez. Read model
once bellek/dosya tabanli ve yeniden uretilebilir olur; DB ancak is hacmi ve query
suresi esikleriyle kanitlanirsa eklenir.

### 7.6 Route ve API modeli

| API | Amac | Yetki | Yazma |
| --- | --- | --- | --- |
| `GET /api/v1/control/summary` | Bugun ekraninin tek ozet payload'i | operator/admin | Hayir |
| `GET /api/v1/control/work-items` | Filtreli is listesi | operator/admin | Hayir |
| `GET /api/v1/control/work-items/{id}` | Is, handoff ve evidence ozeti | operator/admin | Hayir |
| `GET /api/v1/control/agents` | Ajan durumu ve heartbeat | operator/admin | Hayir |
| `GET /api/v1/control/approvals` | Bekleyen kararlar | operator/admin | Hayir |
| `GET /api/v1/control/system` | Servis/CI/veri akis sagligi | operator/admin | Hayir |
| `GET /api/v1/control/reports/{period}` | Gunluk/haftalik rapor | operator/admin | Hayir |
| `POST /api/v1/control/intents` | Allowlist'li operator talebi | admin + CSRF/replay | Inbox intent |

Tum Control API endpointleri mevcut `optional_auth` kalibini degil, en az
`require_admin` veya ayri `require_operator` bagimliligini kullanir. `/ops` route'u
server/middleware seviyesinde de korunur; yalniz client-side `isAdmin` kontrolune
guvenilmez. Ham aday listesi, premium alanlar ve secret degerler read modeline girmez.

### 7.7 Olay esleme

| Kaynak olayi | Web gorunumu / intent | Yon |
| --- | --- | --- |
| Work Item created/updated | Is listesi/detay karti | Repo -> projector -> web |
| Handoff ready | Hedef ajan ve Onaylar bildirimi | Repo -> projector -> web |
| Copilot/Claude Code/Claude Cowork accepted | Ajan karti + accepted durumu | Repo -> projector -> web |
| CI completed | Evidence ozeti | GitHub -> repo evidence -> web |
| Meric create/assign/priority | Operator intent | Web -> inbox -> repo validator |
| Meric onay/red | Approval intent | Web -> inbox -> repo'da ayri onay kaydi |
| Publish sonucu | Salt-okunur delivery metadata | FinPilot -> web |

Cockpit iki kontrollu surumde acilir:

1. **Cockpit v1 - read-only:** Repo -> Control Center projection, dashboard ve raporlar.
2. **Cockpit v2 - controlled intent:** Yalniz create, assign, priority,
   acknowledge, approve, reject ve request_changes. Kimlik, replay/idempotency,
   policy ve audit testlerinden sonra.

Publish, deploy, secret, scanner/risk ve broker aksiyonlari Cockpit v2'de de yoktur.

### 7.8 Idempotency ve korelasyon

Her dis olay su alanlari tasir:

```json
{
  "event_id": "EVT-uuid",
  "work_item_id": "WI-20260802-001",
  "handoff_id": "HO-20260802-001",
  "source": "repo",
  "event_type": "handoff.ready",
  "occurred_at": "2026-08-02T00:00:00Z",
  "payload_sha256": "..."
}
```

Projector ayni `event_id`'yi ikinci kez islememelidir. Web read modelindeki kayit
canonical repo locator'ini tasir; gorunum icerigi otorite olarak geri kopyalanmaz.

### 7.9 Yetkilendirme ve web guvenligi

Control Center musteri dashboard'undan ayri bir guvenlik alani olarak ele alinir:

- `/ops` ve tum Control API endpointleri default-deny olur.
- Read endpointleri dahil operator/admin kimligi ister.
- Yazma intent'lerinde CSRF, nonce, timestamp, idempotency key ve audit zorunludur.
- Tarayicida secret, model key, broker credential veya private key tutulmaz.
- Session suresi, yeniden kimlik dogrulama ve logout davranisi pilotta test edilir.
- Hassas eylemde buton etiketi sonucu aciklar; genel `Devam` kullanilmaz.
- Level B onayinda evidence ozeti zorunlu; Level C icin web uygulama butonu yoktur.
- Her red/degisiklik talebinde gerekce zorunludur.

Mevcut browser `localStorage` token modeli operasyon yuzeyi icin risk analizi
gerektirir. HttpOnly/SameSite cookie veya kisa omurlu operator session'a gecis
ayri Level B guvenlik karari olarak pilot oncesi degerlendirilir.

### 7.10 Yerel Agent Bridge ve opsiyonel Buzz

Ilk surum ajanlari web'den dogrudan baslatmaz; gorev atar, durumu ve kaniti izler.
Web'den ajan baslatma/durdurma ancak resmi ve desteklenen arayuzlerle ayri bir Local
Agent Bridge fazinda ele alinir:

- Claude Code icin CLI/ACP destek matrisi ve process izolasyonu
- Claude Cowork icin desteklenen gorev alma/cikti verme arayuzu
- GitHub Copilot icin yalniz resmi otomasyon yuzeyi varsa adapter
- Her ajan icin ayri kimlik, workspace ve izin profili
- Kill switch, timeout, heartbeat ve orphan process temizligi
- Ayni Work Item icin tek yazar/worktree kilidi

Desteklenmeyen editor UI otomasyonu veya browser tiklatma kullanilmaz. Buzz daha
sonra Slack/Telegram benzeri salt-okunur bildirim ve mobil inbox adaptoru olarak
eklenebilir; ana cockpit veya otorite olmaz.

---

## 8. Veri siniflandirma ve redaksiyon

| Sinif | Ornek | Repo Work Item | Control Center | Opsiyonel dis bildirim |
| --- | --- | ---: | ---: | ---: |
| Public | Dokuman yolu, commit SHA, test sayisi | Evet | Evet | Evet |
| Internal | Mimari not, hata ozeti, diff ozeti | Evet | Evet | Ozet/redakte |
| Sensitive | Aday listesi, premium snapshot, kullanici e-postasi | Referans, maskeli | Gerektikce/maskeli | Hayir |
| Secret | API key, token, parola, private key | Hayir | Hayir | Hayir |
| Restricted | Broker credential, emir niyeti, canli risk ayari | Hayir | Hayir | Hayir |

Redaksiyon kurallari:

- Env degerleri asla serialize edilmez.
- E-posta/Telegram ID raporlarda maskelenir.
- Komut ciktisi gonderilmeden token-benzeri diziler taranir.
- Diff'in tamami yerine dosya yolu + commit SHA + test sonucu gonderilir.
- Financial user-facing content yalniz mevcut lint ve preview kapisindan gecer.

---

## 9. Fazli uygulama yol haritasi

### Faz 0 - Baseline ve karar dondurma (1-2 gun, Level A analiz)

Isler:

1. Bu plan icin Meric karari: repo-native omurga + FinPilot-native Control Center.
2. Aktor adlari ve Level A/B/C gecis tablosunu onayla.
3. Ilk pilot use case'ini sec: **Control Center'da Work Item -> Claude Cowork
  arastirma -> VS Code'da Copilot veya Claude Code uygulama -> Control Center'da durum/kanit ozeti ->
  Meric review**.
4. Mevcut `AGENTS.md` DRAFT durumu ve acik governance onaylarini netlestir.
5. `/ops` operator kimligi, session ve veri siniflandirma kararini ver.

Cikis kriteri:

- Tek pilot use case
- Tek owner
- Kabul kriteri
- Control Center veri sinifi, route'lari ve ekranlari
- VS Code'da kullanilacak yurutucu ve task'lar
- Hangi verinin web read modeline girecegi yazili
- Publish/broker/secrets kapsam disi

### Faz 1 - Repo-native contract (2-3 gun, Level B)

Isler:

1. `.finpilot/schemas/` altinda uc JSON Schema.
2. `scripts/handoff.py validate/list/show/create/accept/transition` CLI.
3. Deterministik ID ve UTC timestamp.
4. Level gecis validator'u.
5. Secret/redaction validator'u.
6. Ornek bir Work Item'i uctan uca devret.

Testler:

- Zorunlu alan ve enum dogrulamasi
- Level B onaysiz `done` reddi
- Level C'nin ajan tarafindan `applied/done` yapilamamasi
- Gecersiz owner transition reddi
- Secret-benzeri alanin reddi
- Ayni handoff/event ID'sinin idempotent olmasi
- Windows path ve UTF-8 uyumu

Cikis kriteri:

- VS Code Copilot, Claude Code ve Claude Cowork ayni dosyayi okuyup yazabiliyor
- Bir devir yalnizca paketle tamamlanabiliyor
- Kanitsiz `done` reddediliyor
- Mevcut production testlerine etkisi yok

### Faz 2 - FinPilot web read-only cockpit v1 (3-5 gun, Level B)

Isler:

1. Ayri `/ops` layout'u ve default-deny operator route guard'i kur.
2. `control_projector.py`, yeniden uretilebilir read model ve stale-state kontrolu olustur.
3. `summary`, `work-items`, `agents`, `approvals`, `system` read endpointlerini kur.
4. Bugun, Onaylar, Ajanlar, Blokajlar ve Sistem Sagligi bloklarini uret.
5. Payload allowlist, boyut siniri ve secret redaction uygula.
6. Reconciler ile repo/read-model drift'ini bul ve web'i repo gercegine geri getir.
7. Web/API kesikken repo-native akisin calistigini test et.

Kabul kriteri:

- Work Item/Handoff olayi 60 saniye icinde dogru kart/listede gorunur
- Ayni event tekrar islendiginde duplicate kart/transition olusmaz
- Web kapaliyken Work Item ve muhendislik akisi kayip vermeden devam eder
- Ham diff, tam log, secret, snapshot, PII ve broker verisi read modeline girmez
- Drift otomatik bulunur ve repo degeri kazanir
- Bu fazda web'den repo'ya hicbir state transition yapilamaz

### Faz 3 - VS Code workbench ve yurutucu protokolleri (2-3 gun, Level B)

Isler:

1. `AGENTS.md` acilisina "aktif Work Item + son accepted Handoff" adimi oner.
2. `.vscode/tasks.json` icinde handoff listeleme/gosterme/dogrulama, focused test ve
  evidence kontrol task'larini tanimla.
3. `.vscode/extensions.json` icinde yalniz gerekli/onerilen entegrasyonlari belgeleyip
  pinleme ve guvenlik politikasini belirle.
4. GitHub Copilot icin role profile: VS Code icinde code/test/review.
5. Claude Code icin role profile: VS Code terminali/entegrasyonu icinde code/test/review.
6. Claude Cowork icin role profile: research/docs/corpus/planning/operations.
7. Handoff sablonlari:
   - research -> implementation
   - implementation -> review
   - incident -> root cause
   - plan -> execution
8. Her session sonunda `next_action`, `blockers`, `evidence` zorunlulugu.
9. VS Code acilis kontrolu: workspace trust, aktif branch/worktree, dirty files,
  Python environment ve gerekli extension durumu.

VS Code minimum workbench gorunumu:

- Explorer: `.finpilot/` + aktif kod/dokuman
- Source Control: aktif Work Item diff'i
- Problems: compile/lint/type diagnostics
- Test Explorer veya focused test task'i
- Terminal: tekrar uretilebilir komut ve cikti
- Copilot Chat/Agent veya Claude Code: yalniz atanmis yurutucu

Bir isi iki ajan birlikte inceleyebilir; ancak ayni anda tek `owner` yazma yetkisine
sahiptir. Diger ajan reviewer veya sonraki Handoff hedefidir.

Kabul senaryosu:

```text
Meric Control Center'da Work Item formunu doldurur; v1 pilotunda validator ile repo kaydi olusturulur
  -> Claude Cowork kaynakli bulgu paketi olusturur
  -> VS Code'da secilen yurutucu (Copilot veya Claude Code) kabul eder
  -> ayri branch/worktree'de uygular
  -> Problems + focused test + diff evidence ekler
  -> Control Center kanit ozetini ve bekleyen onayi gosterir
  -> Meric gerektiginde VS Code Source Control ve test sonucuna inerek review eder
  -> Claude Cowork dokuman tutarliligini kontrol eder
  -> Level B onayla done olur
```

Kabul kriterleri:

- VS Code acildiginda aktif Work Item tek task ile gorulebiliyor
- Handoff ve schema validation terminal komutu ezberlemeden calistirilabiliyor
- Problems veya focused test basarisizsa `done` olamiyor
- Copilot ve Claude Code ayni Work Item'i okuyabiliyor; owner cakismasi reddediliyor
- VS Code kapansa bile state repodaki `.finpilot/` kayitlarindan geri kuruluyor

### Faz 4 - GitHub/CI evidence bridge (2-4 gun, Level B)

Isler:

1. Commit/PR body'de Work Item ID validator'u.
2. CI sonucu icin evidence kaydi veya artifact.
3. Degisen dosya ve test komutu otomatik ozetleme.
4. Basarisiz CI'da Work Item `blocked/review` kalir.
5. Main'e merge yalniz korumali insan/PR akisi ile.
6. VS Code Source Control'daki local evidence ile uzak CI sonucunu ayni Work Item'a
  korele et.

Kabul kriteri:

- Commit -> Work Item -> Handoff -> test kaniti izlenebiliyor
- CI basarisizken `done` olamiyor
- Unrelated dirty worktree dosyalari handoff'a karismiyor

### Faz 5 - Cockpit raporlari ve alarm kurallari (2-4 gun, Level B)

Isler:

1. Append-only eventlerden gunluk ozet ve haftalik metrikleri hesapla.
2. `unknown`/eksik veri semantigini uygula; metrik uydurma veya sifir sayma.
3. 24 saat blokaj, stale heartbeat, CI failure ve projection drift alarmlarini kur.
4. Rapor satirindan Work Item/evidence locator'ina gecisi sagla.
5. Baseline haftayi kaydet; hedefleri ancak baseline sonrasinda dondur.

Kabul kriteri:

- Gunluk ve haftalik rapor ayni event setinden tekrar uretilebiliyor
- Toplamlar canonical Work Item kayitlariyla uzlasiyor
- Eksik veri acikca `unknown` gorunuyor
- Her alarm owner, zaman ve kaynak Work Item/event tasiyor
- Raporlar ajanlari yalniz ham is sayisiyla siralamiyor

### Faz 6 - Web controlled intent v2 (3-5 gun, Level B/C)

On kosul: Read-only cockpit ve raporlar en az 10 is gunu temiz; Meric ayri onayi.

Isler:

1. Reaction/komut -> signed intent inbox.
2. Kimlik, nonce, timestamp, replay ve idempotency kontrolu.
3. Yalniz `create`, `assign`, `priority`, `acknowledge`, `approve`, `reject` ve
  `request_changes` aksiyonlari.
4. Publish komutu yok; publish ayri Level C akisinda kalir.
5. Her geri yazma append-only audit olayi uretir.

Kabul kriteri:

- Yetkisiz kanal/ajan reaction'i reddedilir
- Replay reddedilir
- Web karti veya request payload'i tek basina otorite dosyasini degistiremez
- Meric onayi kimlik ve evidence ile izlenir
- Level C intent `applied/done` durumuna gecemez
- Publish/deploy/scanner-risk/broker komutlari semada dahi tanimli degildir

### Faz 7 - Urun-ici ajan event bridge (3-5 gun, Level B)

Isler:

1. `agent_events` ve `signal_events` icin disariya acilacak allowlist alanlari.
2. Scan, academy ve distribution olaylarini metadata-only normalize et.
3. Work Item ile product cycle arasinda `correlation_id` kur.
4. Control Center'a yalniz operasyon durumu gonder.
5. Serbest metin handoff'un urun ajanina dogrudan girmesini yasakla.

Kabul kriteri:

- `work_item_id -> cycle_id -> snapshot_id -> delivery_id` zinciri kurulabiliyor
- Finansal contract alanlari ve ham payload disari sizmiyor
- Urun ajanlari Control Center arizasindan etkilenmiyor

### Faz 8 - Operasyonellestirme ve Go/No-Go (10 is gunu pilot, Level B)

Olcumler:

- Handoff kabul suresi
- Baglam tekrar anlatma suresi
- Control Center acilisindan kritik durumlari anlamaya kadar gecen sure
- Bekleyen onayin fark edilme ve sonuclanma suresi
- VS Code acilisindan aktif Work Item'i gormeye kadar gecen sure
- Task ile calistirilan dogrulama orani
- Eksik kanit nedeniyle geri donen is orani
- Concurrent worktree cakismasi
- Yanlis/eskimis dokuman referansi
- Projector/API basari orani
- Repo/read-model reconciliation farki ve duzelme suresi
- Claude Cowork research handoff kabul ve geri-donus orani
- Manual approval bypass denemesi/sayisi

Go kriterleri:

- Handoff'larin >=%90'i zorunlu alanlari ilk seferde gecer
- Baglam tekrar anlatma suresi baseline'a gore >=%50 azalir
- 0 secret/sensitive veri ihlali
- 0 publish/merge approval bypass
- Control Center kesinti testi basarili
- Repo ve read model durum uyusmazligi otomatik tespit edilir

No-Go:

- Control Center yeni tek gercek kaynagi haline geliyorsa
- Ajanlar ayni worktree'de birbirinin degisikliklerini eziyorsa
- Onay reaction'i publish'e dogrudan baglandiysa
- Read modele ham snapshot, secret veya gereksiz user data gidiyorsa
- Handoff yazma maliyeti isten daha buyukse ve olcum bunu dogruluyorsa

---

## 10. Ilk pilot icin somut backlog

| ID | Is | Sahip | Level | Bagimlilik | Cikis |
| --- | --- | --- | --- | --- | --- |
| OB-01 | Work Item/Handoff/Evidence v1 semasini dondur | Ortak | B | Meric onayi | 3 schema |
| OB-02 | Stdlib `handoff.py` validator CLI | Claude Code | B | OB-01 | Testli CLI |
| OB-03 | Secret/redaction policy testleri | Claude Code | B | OB-02 | Negatif testler |
| OB-04 | `/ops` auth/session/data-classification threat model | Claude Cowork | A | OB-01 | Guvenlik karari |
| OB-05 | Repo event projector ve payload allowlist | Claude Code | B | OB-02..04 | Redakte read model |
| OB-06 | Control API read endpointleri | Claude Code | B | OB-05 | Admin-gated API |
| OB-07 | `/ops` layout, Bugun ve detay cekmecesi | GitHub Copilot | B | OB-06 | Read-only cockpit |
| OB-08 | Repo/read-model reconciler | Claude Code | B | OB-07 | Drift alarmi/onarimi |
| OB-09 | VS Code handoff/validation/test task'lari | GitHub Copilot | B | OB-02 | `.vscode/tasks.json` |
| OB-10 | VS Code extension/workspace guvenlik listesi | Meric + Copilot | B | OB-09 | `.vscode/extensions.json` |
| OB-11 | Claude Cowork, Copilot ve Claude Code role/handoff sablonlari | Ilgili aktorler | A | OB-01 | 3 role profile/template |
| OB-12 | Control Center -> Claude Cowork -> VS Code -> Control Center kuru prova | Meric + aktorler | A | OB-07..11 | Evidence zinciri |
| OB-13 | GitHub/CI Work Item referansi | GitHub Copilot | B | OB-12 | CI guard |
| OB-14 | Gunluk/haftalik report generator | Claude Cowork + Copilot | B | OB-08, OB-13 | Tekrar uretilebilir rapor |
| OB-15 | Ajan heartbeat ve stale/blocker alarmlari | Claude Code | B | OB-07 | Agent Board |
| OB-16 | 10 is gunu cockpit v1 pilot scorecard | Claude Cowork | A | OB-14..15 | Go/No-Go raporu |
| OB-17 | Signed intent inbox ve quarantine | Claude Code | B/C | OB-16 + onay | Sinirli geri yazma |
| OB-18 | Intent identity/nonce/replay/policy testleri | GitHub Copilot | B/C | OB-17 | Negatif test paketi |
| OB-19 | Urun runtime metadata bridge | Claude Code | B | OB-16 | Allowlist'li operasyon olaylari |
| OB-20 | Responsive/keyboard/accessibility UX testleri | GitHub Copilot | B | OB-07 | Desktop/mobile kanit |
| OB-21 | Opsiyonel Local Agent Bridge fizibilitesi | Claude Cowork + Claude Code | B | OB-16 | Resmi API destek matrisi |

Ilk cockpit pilotu **OB-01..OB-16** kapsar ve write-back kapali kalir. **OB-17..18**
yalniz read-only pilot Go karari ve Meric'in ayri Level B/C onayindan sonra acilir.

---

## 11. Test stratejisi

### Contract testleri

- JSON Schema backward compatibility
- Zorunlu otorite ve decision-level alanlari
- Unknown schema version fail-closed
- Timestamp UTC ve ID uniqueness

### Governance testleri

- Level B/C transition guard
- Human approver allowlist
- Decision reference yoksa governance etkili is `done` olamaz
- Product/risk kural catismasi varsa `blocked`

### Security testleri

- Token/key/password benzeri alan redaksiyonu
- `.env` ve private-key path allowlist disi
- Control API/read-model payload allowlist
- `/ops` default-deny route ve server-side role guard
- CSRF/session expiry/replay/idempotency
- Log/diff boyut siniri

### Entegrasyon testleri

- VS Code task'lari Windows/PowerShell ortaminda temiz calisir
- VS Code yeniden acildiginda aktif Work Item repodan geri kurulur
- GitHub Copilot ve Claude Code ayni Work Item semasini kabul eder
- Claude Cowork -> VS Code yurutucusu -> Meric -> Claude Cowork round-trip
- Iki yurutucunun ayni Work Item'i owner olarak kabul etmesi reddedilir
- Problems/focused test failure -> review/done reddi
- CI failure -> blocked
- Control Center unavailable -> repo akisi devam
- Duplicate event -> tek mesaj/tek transition
- Out-of-order event -> eski state cockpit kartini geriye goturemez
- Read-model/repo drift -> repo degeriyle otomatik reconciliation
- Forged/stale/replayed intent -> quarantine + audit, sifir transition
- Yetkili ama allowlist disi intent -> fail-closed
- Stale Handoff -> reject/supersede

### Finansal guvenlik testleri

- Handoff scanner score/entry/risk degerini dogrudan degistiremez
- Control Center intent'i publish cagiramaz
- Broker/execution endpoint'i adapter credential'i ile erisilemez
- Snapshot/Telegram yine ayni mevcut publish gate'ten gecer

---

## 12. Operasyon ritueli

### Gun baslangici - 2 dakika

1. Control Center `Bugun` ekraninda Onaylar, Blokajlar ve Sistem Sagligi'ni kontrol et.
2. Gunluk raporda ilk uc onceligi ve owner'larini belirle.
3. Calisilacak Work Item detayini ac; v2 sonrasi owner/priority intent'ini ver.
4. Teknik is varsa Work Item locator'i ile VS Code workspace'ini ac.
5. VS Code'da trust, Python environment, dirty worktree ve branch/worktree
  sahipligini kontrol et; tek yurutucuyu sec.

### Is sirasinda

- Buyuk sohbet ozeti yerine Work Item guncellenir.
- Yeni varsayim `assumptions` alanina eklenir.
- Catismada is `blocked` olur; ajan sessiz karar vermez.
- Problems, focused test, diff, commit ve rapor evidence olarak baglanir.
- Yurutucu degisecekse once Handoff yazilir; sohbet kopyalayarak devir yapilmaz.
- Control Center yalniz ozet gosterir; teknik uygulama ve validation VS Code'da yapilir.

### Is sonu

1. VS Code'da ne degisti ve ne dogrulandi?
2. Ne dogrulanamadi; hangi risk/karar acik?
3. Sonraki tek aksiyon ve sahibi kim?
4. Level B/C ise Meric review durumu nedir?
5. VS Code Source Control, Problems ve test gorunumu temiz mi?
6. Control Center karti ve evidence ozeti canonical repo state'iyle uyumlu mu?
7. Gun sonu cockpit ozetinde sahipsiz/bloklu is var mi?

Bu yedi soru olmadan handoff tamamlanmis sayilmaz.

---

## 13. Maliyet ve isletim degerlendirmesi

### Repo-native katman

- Ilk uygulama: yaklasik 4-7 muhendislik gunu
- Isletim: dusuk; Git + Python stdlib + mevcut CI
- Vendor lock-in: yok
- En buyuk risk: disiplin uygulanmazsa semalar bayat kalir

### VS Code workbench

- Ilk uygulama: yaklasik 1-2 muhendislik gunu; task ve extension onerileri
- Isletim: dusuk; mevcut VS Code, terminal, SCM, Problems ve test yuzeyleri
- Ozel extension: ilk pilotta yok
- En buyuk risk: Copilot ve Claude Code'un ayni worktree'de eszamanli yazmasi

### FinPilot-native Control Center

- Ilk uygulama: yaklasik 6-10 muhendislik gunu; read-only `/ops`, Control API,
  projector, temel responsive UX ve guvenlik testleri
- Isletim: mevcut Next.js/FastAPI deployment'i uzerinde; yeni relay/DB ilk pilotta yok
- Vendor lock-in: dusuk; canonical contract repo-native
- En buyuk risk: musteri dashboard'u ile operator yuzeyinin auth veya bilgi
  mimarisi seviyesinde birbirine karismasi

### Claude Cowork entegrasyonu

- Ilk uygulama: role profile, research handoff sablonu ve kaynak evidence kurallari
- Model/kullanim maliyeti secilen Claude plani ve gorev hacmine baglidir; bu belgede
  dogrulanmis fiyat verisi yoktur
- En buyuk risk: arastirma ciktisinin kanitsiz sekilde urun veya risk kuralina girmesi

### Deger hipotezi

Sistem ancak su olculurse degerlidir:

- Daha az baglam tekrari
- Daha az ayni dosyada cakisma
- Daha hizli review
- Daha eksiksiz evidence
- Daha az "kim ne yapti / proje nerede" belirsizligi

Bu metrikler iyilesmiyorsa web cockpit genisletmesi durdurulur; repo-native handoff
protokolu korunur. Buzz ancak ayrica kanitlanan bildirim ihtiyaci icin degerlendirilir.

---

## 14. Karar kapilari

### Kapi A - Mimari onay (Level B)

Karar:

- Repo ortak beyin mi?
- FinPilot `/ops` Meric'in kontrol kokpiti mi?
- VS Code ana muhendislik calisma ortami mi?
- GitHub Copilot ile Claude Code ayri yurutuculer olarak ayni contract'i mi kullanir?
- Claude Cowork arastirma/operasyon yurutucusu olarak ayni contract'i mi kullanir?
- Dosya + JSON Schema v1 mi?
- Control Center yalniz gorunum/intent katmani olup otorite repo'da mi kalir?
- Ilk pilot Control Center -> Claude Cowork -> VS Code -> Control Center/Meric mi?

### Kapi B - Web, kimlik ve veri siniri (Level B)

Karar:

- `/ops` ayni deployment'ta mi, ayri internal deployment'ta mi?
- `require_operator` rolu ve session modeli ne olacak?
- Hangi read-model payload allowlist'i ve retention uygulanacak?
- Claude Code/Claude Cowork credential sahipligi ve secret store nerede olacak?

### Kapi C - Geri yazma ve onay (Level B/C)

Karar:

- Web intent'i hangi sinirli durumlari degistirebilir?
- Kimlik ve replay korumasi?
- Publish neden kapsam disi kalir?

### Kapi D - Production baglantisi (Level C)

Karar:

- Herhangi bir publish/deploy/financial aksiyon baglanacak mi?

Varsayilan cevap: **Hayir.** Bu plan VS Code ajanlarina, Control Center'a veya
Claude Cowork'a production publish/emir yetkisi vermez.

---

## 15. Nihai onerilen sira

```text
1. Mimari, `/ops` kimligi ve veri sinirini onayla
2. Work Item/Handoff/Evidence semasi ile repo-native CLI'yi kur
3. `/ops` read-only projector, Control API, reconciler ve Bugun ekranini kur
4. VS Code task'lari, workspace guvenligi ve owner kurallarini etkinlestir
5. Control Center -> Claude Cowork -> tek VS Code yurutucusu -> Meric kuru provasini yap
6. Git/CI evidence zincirini bagla
7. Gunluk/haftalik rapor ile agent/blocker alarmlarini kur
8. Cockpit v1'i 10 is gunu read-only pilotta olc
9. Go kararindan sonra signed intent inbox'i ayri onaya sun
10. Sinirli controlled intent v2'yi negatif guvenlik testleriyle ac
11. Gerekiyorsa allowlist'li urun runtime metadata bridge'ini bagla
12. Publish/deploy/scanner-risk/broker yetkisini baglama
```

Bu sirayla FinPilot Control Center Meric'in gunluk kontrol kokpiti, VS Code
muhendislik workbench'i olur; ortak beyin yine repoda kalir. GitHub Copilot,
Claude Code, Claude Cowork ve FinPilot ajanlari ayni gercegi kullanir. Hicbir arac
insan onay kapisini asmaz.

---

## 16. Bu belge icin durum

- **Dogrulandi:** Repoda ortak bootstrap, karar sicili, ajan contract'i, urun
  pipeline'i ve birden fazla olay/audit mekanizmasi var.
- **Dogrulandi:** Genel amacli Work Item/Handoff/Evidence sozlesmesi yok.
- **Dogrulandi:** VS Code ana calisma ortami olmasina ragmen repo'da ortak handoff
  task'i, `.vscode/tasks.json` veya `.code-workspace` konfigurasyonu yok.
- **Dogrulandi:** Mevcut Next.js dashboard, auth context, otonomi onay/audit sayfasi
  ve FastAPI admin endpoint kaliplari native Control Center icin yeniden kullanilabilir.
- **Dogrulandi:** Mevcut otonomi read endpointleri `optional_auth` kullaniyor;
  `/ops` icin bu yeterli degil, server-side operator/admin guard gerekiyor.
- **Oneri:** Repo-native, dosya tabanli v1 omurga.
- **Oneri:** VS Code'u ana muhendislik workbench'i; GitHub Copilot ve Claude Code'u ayri,
  tek-owner kuralli yurutuculer olarak konumlandirma.
- **Oneri:** FinPilot web icinde ayri, sade ve default-deny `/ops` yuzeyi kurma.
- **Oneri:** Buzz'i yalniz ihtiyac kanitlanirsa bildirim adaptoru olarak ekleme.
- **Oneri:** GitHub Copilot, Claude Code ve Claude Cowork icin ortak ama rol-sinirli
  handoff protokolu.
- **Karar bekliyor:** Faz 1 ve sonrasi Level B uygulama onayi.
- **Level C siniri:** Publish, deploy, secrets, broker/emir ve governance authority
  degisiklikleri bu planla otomatiklesmez.
