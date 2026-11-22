"""Free-form answers through Groq's chat completions API.

Used as the fallback when the deterministic rules do not match and the RAG
pipeline has no knowledge base yet. Returns None when no Groq key is configured
or the request fails, so callers can keep their own fallback text.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

CHAT_TIMEOUT_SECONDS = 30
MAX_TOKENS = 350

SYSTEM_PROMPT = (
    "You are LimkoBot, the WhatsApp assistant for Limkokwing University in "
    "Sierra Leone (Freetown campus). Answer briefly and helpfully, in WhatsApp "
    "style (short paragraphs, no markdown tables).\n"
    "Always reply in the same language or dialect the student used, including "
    "Krio or English-Krio mix.\n"
    "Known facts: application fee is USD 100; 2026 final exams run 8-19 June; "
    "registration is online through the student portal before semester start; "
    "programmes include diplomas, degrees and postgraduate courses in computing, "
    "design, business, communication and architecture.\n"
    "If you are unsure, say so and offer the menu: 1 = Fees, 2 = Exam schedule, "
    "3 = Registration, 4 = Programmes, 5 = Support. Do not invent fees, dates or "
    "requirements, and do not discuss topics unrelated to the university."
)


def answer(question: str, context: str | None = None) -> str | None:
    question = (question or "").strip()
    if not question or not settings.GROQ_API_KEY:
        return None

    user_content = question
    if context:
        user_content = f"Context:\n{context}\n\nStudent question: {question}"

    url = f"{settings.GROQ_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}
    payload = {
        "model": settings.GROQ_LLM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.3,
        "max_tokens": MAX_TOKENS,
    }

    try:
        with httpx.Client(timeout=CHAT_TIMEOUT_SECONDS) as client:
            response = client.post(url, headers=headers, json=payload)
    except Exception:  # noqa: BLE001 - fallback is best-effort
        logger.exception("Groq chat request failed")
        return None

    if response.status_code >= 400:
        logger.warning(
            "Groq chat HTTP %s (model=%s): %s",
            response.status_code,
            settings.GROQ_LLM_MODEL,
            response.text[:300],
        )
        return None

    try:
        choices = response.json().get("choices") or []
        content = (choices[0].get("message") or {}).get("content") or ""
    except Exception:  # noqa: BLE001 - fallback is best-effort
        logger.exception("Groq chat response was not usable")
        return None

    return content.strip() or None
