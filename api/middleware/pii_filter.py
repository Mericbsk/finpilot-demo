"""Presidio-based PII detection and scrubbing middleware.

Scope:
- FastAPI middleware: sanitizes JSON response bodies on LLM endpoints
- Standalone `scrub()` util: use anywhere to mask PII in a string
- Turkish custom recognizers: TR IBAN, TC Kimlik No

Supported PII types (auto-detected):
  PERSON, EMAIL_ADDRESS, PHONE_NUMBER, IBAN_CODE, CREDIT_CARD,
  IP_ADDRESS, LOCATION, DATE_TIME, TR_IBAN, TR_NATIONAL_ID

Usage in main.py:
  from api.middleware.pii_filter import PIIFilterMiddleware
  app.add_middleware(PIIFilterMiddleware)
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Presidio bootstrap — lazy init so import doesn't crash if not installed
# ---------------------------------------------------------------------------
_analyzer = None
_anonymizer = None

_LLM_PATH_PREFIX = "/api/v1/llm"

_DEFAULT_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "IBAN_CODE",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "LOCATION",
    "DATE_TIME",
]


def _build_engine():
    global _analyzer, _anonymizer
    if _analyzer is not None:
        return

    try:
        from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
        from presidio_anonymizer import AnonymizerEngine

        analyzer = AnalyzerEngine()

        # Turkish IBAN: TR + 24 digits
        tr_iban = PatternRecognizer(
            supported_entity="TR_IBAN",
            patterns=[Pattern(name="tr_iban", regex=r"\bTR\d{24}\b", score=0.95)],
        )
        # TC Kimlik No: exactly 11 digits, first digit non-zero
        tc_kimlik = PatternRecognizer(
            supported_entity="TR_NATIONAL_ID",
            patterns=[Pattern(name="tc_kimlik", regex=r"\b[1-9]\d{10}\b", score=0.6)],
        )
        analyzer.registry.add_recognizer(tr_iban)
        analyzer.registry.add_recognizer(tc_kimlik)

        _analyzer = analyzer
        _anonymizer = AnonymizerEngine()

    except ImportError:
        logger.warning(
            "presidio-analyzer/presidio-anonymizer not installed — PII filter disabled. "
            "Run: pip install presidio-analyzer presidio-anonymizer"
        )


def scrub(text: str, language: str = "en") -> str:
    """Return `text` with all detected PII replaced by <ENTITY_TYPE> placeholders.

    Safe to call even when Presidio is not installed (returns text unchanged).
    """
    _build_engine()
    if _analyzer is None or not text:
        return text

    entities = _DEFAULT_ENTITIES + ["TR_IBAN", "TR_NATIONAL_ID"]
    try:
        results = _analyzer.analyze(text=text, language=language, entities=entities)
        if not results:
            return text
        return _anonymizer.anonymize(text=text, analyzer_results=results).text
    except Exception:
        logger.exception("PII scrubbing failed — returning original text")
        return text


def _scrub_value(value: Any) -> Any:
    if isinstance(value, str):
        return scrub(value)
    if isinstance(value, dict):
        return {k: _scrub_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub_value(item) for item in value]
    return value


class PIIFilterMiddleware(BaseHTTPMiddleware):
    """Starlette/FastAPI middleware that scrubs PII from LLM endpoint responses.

    Only intercepts paths starting with /api/v1/llm to keep overhead minimal.
    All other endpoints pass through unmodified.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if not request.url.path.startswith(_LLM_PATH_PREFIX):
            return response

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        try:
            data = json.loads(body)
            clean = _scrub_value(data)
            clean_body = json.dumps(clean, ensure_ascii=False).encode()
        except Exception:
            clean_body = body

        return Response(
            content=clean_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type="application/json",
        )
