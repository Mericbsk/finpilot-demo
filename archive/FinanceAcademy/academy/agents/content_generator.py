"""
AGENT 1 — Content Generator Agent
===================================
Yeni ders, flashcard, quiz ve case study üretir.
LLM'i pedagojik şablonla yönlendirir, JSON çıktısını doğrular.

Tetiklenme:
  - Haftalık schedule
  - Gap Detector sinyali
  - Trend Scout sinyali
  - API isteği (kullanıcı konuyu aradı ama bulunamadı)
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta

from academy.domains import DOMAIN_BY_SLUG
from academy.models import (
    AgentLogRepository,
    ContentJob,
    ContentJobRepository,
    Lesson,
    LessonComponent,
    LessonComponentRepository,
    LessonRepository,
)

logger = logging.getLogger(__name__)
AGENT_NAME = "content_generator"


# ─────────────────────────────────────────────────────────────────────────────
# STANDALONE LLM CLIENT (Borsa projesine bağımlı değil)
# Öncelik: 1) Groq HTTP  2) Ollama  3) Borsa router  4) Mock
# ─────────────────────────────────────────────────────────────────────────────


def _load_env():
    """FinanceAcademy/.env dosyasını os.environ'a yükle."""
    env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    env_file = os.path.normpath(env_file)
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, _, v = line.partition("=")
                    k = k.strip()
                    if k and k not in os.environ:
                        os.environ[k] = v.strip()


_load_env()


class _GroqClient:
    """Groq API HTTP istemcisi — hiçbir ek paket gerektirmez."""

    MODELS = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ]

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate(self, prompt: str, **_) -> object:
        for model in self.MODELS:
            try:
                result = self._call(model, prompt)
                if result:
                    return type("R", (), {"content": result})()
            except Exception as e:
                logger.debug("Groq model %s failed: %s", model, e)
        return None

    def _call(self, model: str, prompt: str) -> str | None:
        payload = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 3000,
                "temperature": 0.3,
            }
        ).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        resp = urllib.request.urlopen(req, timeout=60)
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


class _OllamaClient:
    """Ollama yerel model istemcisi — /api/chat + JSON mode kullanır."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate(self, prompt: str, json_mode: bool = True, **_) -> object:
        try:
            payload: dict = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 4096},
            }
            # JSON mode: modeli saf JSON üretmeye zorlar
            if json_mode:
                payload["format"] = "json"

            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=300)
            result = json.loads(resp.read())
            content = result.get("message", {}).get("content", "")
            return type("R", (), {"content": content})()
        except Exception as e:
            logger.debug("Ollama chat error: %s", e)
            # Fallback: /api/generate (eski API)
            return self._generate_fallback(prompt)

    def _generate_fallback(self, prompt: str) -> object | None:
        try:
            payload = json.dumps(
                {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.3},
                }
            ).encode()
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=300)
            data = json.loads(resp.read())
            return type("R", (), {"content": data.get("response", "")})()
        except Exception as e:
            logger.debug("Ollama generate fallback error: %s", e)
            return None


def _list_ollama_models(base_url: str) -> list[str]:
    """Ollama'da yüklü modelleri döndür."""
    try:
        req = urllib.request.Request(f"{base_url}/api/tags")
        resp = urllib.request.urlopen(req, timeout=3)
        data = json.loads(resp.read())
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


# En iyi içerik üretimi için model öncelik sırası
# (büyük/akıllı modeller önce, küçükler sonda)
_MODEL_PRIORITY = [
    "gpt-oss:120b-cloud",
    "deepseek-v3.1:671b-cloud",
    "gpt-oss:120b",
    "qwen3:30b",
    "deepseek-r1:8b",
    "llama3.2:3b",
    "phi3:latest",
    "gemma3:4b",
    "gemma3:1b",
]


def _pick_best_model(available: list[str], requested: str) -> str:
    """Mevcut modeller arasından en iyisini seç."""
    # Kullanıcının istediği model varsa onu kullan
    if requested in available:
        return requested
    # Öncelik sırasına göre ilk uyuşanı seç
    for preferred in _MODEL_PRIORITY:
        if preferred in available:
            return preferred
    # Hiçbiri eşleşmezse listedeki ilki
    return available[0] if available else requested


def _build_llm_client():
    """En uygun LLM istemcisini döndür.

    Öncelik:
      LLM_PROVIDER=ollama → sadece Ollama dene
      LLM_PROVIDER=groq   → sadece Groq dene
      (belirtilmemişse)   → Ollama → Groq → Borsa router → mock
    """
    _load_env()
    provider = os.environ.get("LLM_PROVIDER", "").lower().strip()
    ollama_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.environ.get("OLLAMA_MODEL", "llama3.2")
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()

    def try_ollama():
        models = _list_ollama_models(ollama_url)
        if not models:
            return None
        chosen = _pick_best_model(models, ollama_model)
        print(f"  🦙 Ollama: {chosen}")
        print(f"     Mevcut: {', '.join(models)}")
        logger.info("[%s] LLM: Ollama %s @ %s", AGENT_NAME, chosen, ollama_url)
        return _OllamaClient(ollama_url, chosen)

    def try_groq():
        if not groq_key:
            return None
        print("  ☁️  Groq API kullanılıyor...")
        logger.info("[%s] LLM: Groq API", AGENT_NAME)
        return _GroqClient(groq_key)

    def try_borsa_router():
        try:
            from llm import get_router

            r = get_router()
            logger.info("[%s] LLM: Borsa router", AGENT_NAME)
            return r
        except Exception:
            return None

    if provider == "ollama":
        client = try_ollama()
        if client:
            return client
        print("  ⚠️  Ollama bulunamadı, Groq'a geçiliyor...")
        return try_groq() or try_borsa_router()

    if provider == "groq":
        client = try_groq()
        if client:
            return client
        print("  ⚠️  Groq key yok, Ollama'ya geçiliyor...")
        return try_ollama() or try_borsa_router()

    # Otomatik: Ollama → Groq → Borsa router → None (mock)
    return (
        try_ollama()
        or try_groq()
        or try_borsa_router()
        or (print("  ⚠️  LLM bulunamadı — mock mod aktif") or None)
    )


# ─────────────────────────────────────────────────────────────────────────────
# LLM SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sen FinPilot Finance Academy için Türkçe finansal eğitim içerikleri üreten
uzman bir pedagoji ve finans yazarısın.

Ürettiğin her içerik:
1. Finansal olarak doğru ve güncel olmalı
2. Hedef zorluk seviyesine uygun dil kullanmalı (beginner=sade, advanced=teknik)
3. Gerçek piyasa örnekleri içermeli (ABD borsası veya Türk piyasaları)
4. Pedagojik sırayı takip etmeli: kavram → örnek → yanlış anlama → test
5. Öğrencinin "neden önemli?" sorusunu yanıtlamalı

Formatı kesinlikle JSON olarak ver. Markdown veya açıklama EKLEME, sadece JSON döndür."""

LESSON_TEMPLATE = """Şu konuda bir Finance Academy dersi üret:

Alan (Domain): {domain_name}
Modül: {module}
Başlık: {title}
Zorluk: {difficulty}
Hedef öğrenci: {audience}

JSON formatı (tam olarak bu yapıyı kullan):
{{
  "title": "...",
  "content": "... (Markdown, min 400 kelime, max 800 kelime) ...",
  "key_takeaways": ["...", "...", "..."],
  "misconceptions": ["...", "..."],
  "real_example": {{"ticker": "...", "context": "..."}},
  "estimated_minutes": 10,
  "quiz_questions": [
    {{
      "question": "...",
      "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
      "correct": "A",
      "explanation": "..."
    }}
  ],
  "flashcards": [
    {{"front": "...", "back": "..."}},
    {{"front": "...", "back": "..."}}
  ],
  "pedagogy_notes": "Bu derste hangi öğrenme prensipleri uygulandı?"
}}"""

AUDIENCE_MAP = {
    "beginner": "Hiç yatırım deneyimi olmayan, finansal terimleri bilmeyen kişiler",
    "intermediate": "Temel borsa bilgisi olan, alım-satım yapmaya başlamış yatırımcılar",
    "advanced": "Aktif trader, teknik analiz bilen, derinlemesine analiz yapan kişiler",
}

# ─────────────────────────────────────────────────────────────────────────────
# GENERATOR
# ─────────────────────────────────────────────────────────────────────────────


class ContentGeneratorAgent:
    """Generates Finance Academy lessons using the FinPilot LLM router."""

    def __init__(self):
        self.lesson_repo = LessonRepository()
        self.component_repo = LessonComponentRepository()
        self.job_repo = ContentJobRepository()
        self.log_repo = AgentLogRepository()
        self._llm = None

    @property
    def llm(self):
        """Lazy LLM client — tries Groq HTTP → Ollama → Borsa router → mock."""
        if self._llm is None:
            self._llm = _build_llm_client()
        return self._llm

    # ──────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────────────

    def generate_lesson(
        self,
        domain_slug: str,
        module: str,
        title: str,
        difficulty: str = "intermediate",
        lesson_id: str | None = None,
    ) -> Lesson | None:
        """Generate a single lesson and persist it."""
        t0 = time.perf_counter()
        domain = DOMAIN_BY_SLUG.get(domain_slug)
        if not domain:
            logger.error("Unknown domain slug: %s", domain_slug)
            return None

        # Build lesson ID if not provided
        if not lesson_id:
            slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:30]
            prefix = "".join(w[0].upper() for w in domain_slug.split("-"))[:3]
            lesson_id = f"{prefix}-{slug}"

        # Check for existing
        existing = self.lesson_repo.get(lesson_id)
        if existing and existing.status == "published":
            logger.info("Lesson %s already published, skipping", lesson_id)
            return existing

        prompt = LESSON_TEMPLATE.format(
            domain_name=domain["name"],
            module=module,
            title=title,
            difficulty=difficulty,
            audience=AUDIENCE_MAP.get(difficulty, AUDIENCE_MAP["intermediate"]),
        )

        raw = self._call_llm(SYSTEM_PROMPT, prompt)
        if not raw:
            return None

        parsed = self._parse_lesson_json(raw)
        if not parsed:
            return None

        now = datetime.utcnow().isoformat()
        review_at = (datetime.utcnow() + timedelta(days=90)).isoformat()

        lesson = Lesson(
            id=lesson_id,
            domain=domain_slug,
            domain_id=domain["id"],
            module=module,
            title=parsed.get("title", title),
            difficulty=difficulty,
            content=parsed.get("content", ""),
            estimated_minutes=parsed.get("estimated_minutes", 10),
            key_takeaways=parsed.get("key_takeaways", []),
            misconceptions=parsed.get("misconceptions", []),
            real_example=parsed.get("real_example", {}),
            related_lessons=[],
            status="draft",  # Quality Guard onaylayana kadar draft
            created_at=now,
            updated_at=now,
            next_review_at=review_at,
        )
        self.lesson_repo.save(lesson)

        # Save components
        order = 0
        for q in parsed.get("quiz_questions", []):
            self.component_repo.save(
                LessonComponent(
                    lesson_id=lesson_id,
                    type="quiz",
                    content=q,
                    order_idx=order,
                )
            )
            order += 1

        for card in parsed.get("flashcards", []):
            self.component_repo.save(
                LessonComponent(
                    lesson_id=lesson_id,
                    type="flashcard",
                    content=card,
                    order_idx=order,
                )
            )
            order += 1

        duration_ms = (time.perf_counter() - t0) * 1000
        self.log_repo.log(
            agent_name=AGENT_NAME,
            action="generate_lesson",
            input_summary=f"{domain_slug}/{module}: {title} [{difficulty}]",
            output_summary=f"lesson_id={lesson_id}, {len(parsed.get('quiz_questions',[]))} quizzes, "
            f"{len(parsed.get('flashcards',[]))} flashcards",
            duration_ms=duration_ms,
        )
        logger.info("[%s] Generated lesson: %s (%.0f ms)", AGENT_NAME, lesson_id, duration_ms)
        return lesson

    def process_job(self, job: dict) -> bool:
        """Process a content_jobs row. Returns True on success."""
        job_id = job["id"]
        payload = json.loads(job.get("payload") or "{}")
        self.job_repo.update_status(job_id, "running")

        try:
            lesson = self.generate_lesson(
                domain_slug=payload["domain"],
                module=payload["module"],
                title=payload["title"],
                difficulty=payload.get("difficulty", "intermediate"),
                lesson_id=payload.get("lesson_id"),
            )
            if lesson:
                self.job_repo.update_status(job_id, "done", result={"lesson_id": lesson.id})
                return True
            self.job_repo.update_status(job_id, "failed", error="Generation returned None")
            return False
        except Exception as exc:
            self.job_repo.update_status(job_id, "failed", error=str(exc))
            logger.error("[%s] Job %s failed: %s", AGENT_NAME, job_id, exc)
            return False

    def enqueue(
        self,
        domain: str,
        module: str,
        title: str,
        difficulty: str = "intermediate",
        priority: int = 2,
    ) -> int:
        """Add a generation task to the job queue."""
        return self.job_repo.enqueue(
            ContentJob(
                agent_name=AGENT_NAME,
                job_type="generate",
                payload={
                    "domain": domain,
                    "module": module,
                    "title": title,
                    "difficulty": difficulty,
                },
                priority=priority,
            )
        )

    # ──────────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────────────────

    def _call_llm(self, system: str, user: str) -> str | None:
        """Call LLM and return raw text, or None on failure."""
        if self.llm is None:
            logger.warning("[%s] LLM unavailable — returning mock content", AGENT_NAME)
            return self._mock_lesson_json()
        try:
            full_prompt = f"{system}\n\n{user}"
            response = self.llm.generate(full_prompt, language="tr")
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e:
            logger.error("[%s] LLM call failed: %s", AGENT_NAME, e)
            return None

    def _parse_lesson_json(self, raw: str) -> dict | None:
        """LLM çıktısından JSON çıkar — her tür formatı işler."""
        if not raw or not raw.strip():
            logger.error("[%s] LLM boş yanıt döndürdü", AGENT_NAME)
            return None

        # 1) Markdown code fence temizle (```json ... ``` veya ``` ... ```)
        text = re.sub(r"```(?:json)?\s*", "", raw).strip()
        text = text.replace("```", "").strip()

        # 2) <think>...</think> bloklarını temizle (deepseek-r1 vs.)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        # 3) Doğrudan JSON dene
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 4) İlk { ... } bloğunu bul (en derin kapanış)
        start = text.find("{")
        if start != -1:
            # Brace sayacıyla doğru kapanış parantezini bul
            depth = 0
            for i, ch in enumerate(text[start:], start):
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        candidate = text[start : i + 1]
                        try:
                            return json.loads(candidate)
                        except json.JSONDecodeError:
                            # Trailing comma'ları temizle ve tekrar dene
                            fixed = re.sub(r",\s*([}\]])", r"\1", candidate)
                            try:
                                return json.loads(fixed)
                            except json.JSONDecodeError:
                                break

        # 5) Regex ile JSON blok ara
        for pattern in [
            r'\{[^{}]*"title"[^{}]*\}',  # flat JSON
            r'\{.*?"content".*?\}',  # content field
        ]:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except Exception:
                    pass

        logger.error("[%s] JSON parse edilemedi. Ham çıktı (ilk 500): %s", AGENT_NAME, raw[:500])
        return None

    @staticmethod
    def _mock_lesson_json() -> str:
        """Return a minimal valid lesson JSON for offline/dev mode."""
        return json.dumps(
            {
                "title": "Mock Ders (LLM Bağlantısı Yok)",
                "content": "Bu bir mock içeriktir. LLM bağlantısı kurulduğunda gerçek içerik üretilecek.",
                "key_takeaways": ["Anahtar çıkarım 1", "Anahtar çıkarım 2"],
                "misconceptions": ["Yaygın yanlış anlama örneği"],
                "real_example": {"ticker": "AAPL", "context": "Apple örnek bağlamı"},
                "estimated_minutes": 10,
                "quiz_questions": [
                    {
                        "question": "Örnek soru?",
                        "options": ["A) Seçenek", "B) Seçenek", "C) Seçenek", "D) Seçenek"],
                        "correct": "A",
                        "explanation": "Açıklama",
                    }
                ],
                "flashcards": [
                    {"front": "Kavram", "back": "Tanım"},
                ],
                "pedagogy_notes": "Mock — spaced repetition + active recall",
            }
        )
