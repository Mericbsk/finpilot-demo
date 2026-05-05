# LLM / AI Layer Özeti

## Teknik Tanım

Groq, Claude ve Gemini sağlayıcıları üzerinden yatırım analizi ve açıklama metni üreten AI katmanıdır. Cache ve provider fallback içerir.

## Durum

**Kısmen çalışıyor.** Endpoint kodu hazır; ancak canlı sağlayıcı anahtarıyla end-to-end doğrulama bu denetimde yapılmadı.

## Öne Çıkan Fonksiyonlar

- `llm/router.py`
- `llm/groq_provider.py`
- `llm/claude_provider.py`
- `llm/gemini_provider.py`
- `api/routers/llm.py`

## Ana Bulgular

- Fallback zinciri ve cache iyi bir temel oluşturuyor.
- Prompt yönetimi kod içinde sabit.
- Provider availability ve quota monitoring görünür değil.

## Güvenlik / Uyumluluk

- Secret’lar env tabanlı.
- Promptlara taşınan veriler için redaction/policy görünmüyor.

## Performans / Ölçek

- 30 dakikalık cache maliyet ve hız açısından olumlu.
- Dış API latency ve quota dalgalanması ana risk.

## Puan

| Kriter | Puan |
|--------|------|
| Stabilite | 6 |
| Güvenlik | 5 |
| Performans | 6 |
| Test | 5 |
| Bakım | 5 |
| Teknik Borç | 5 |
| **Toplam** | **5.6 / 10 — C** |

## İlk 3 Aksiyon

1. LLM smoke ve provider availability testleri ekle.
2. Prompt versioning yapısı kur.
3. Quota ve fallback alarmı tanımla.

## Tekrarlama Notu

- **Ne nedir:** Açıklayıcı AI raporları üreten katmandır.
- **Nasıl çalışır:** istek cache’e, sonra provider router’a, sonra parser’a gider.
- **Nasıl test edilir:** status, timeout, fallback ve schema senaryoları denenir.
- **Bir sonraki değerlendirme için not:** maliyet, quota ve latency dağılımı görünür hale getirilmelidir.
