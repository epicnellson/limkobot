"""Free-form answers through Groq's chat completions API.

Used as the fallback when the deterministic rules do not match and the RAG
pipeline has no knowledge base yet. Returns None when no Groq key is configured
or the request fails, so callers can keep their own fallback text.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

CHAT_TIMEOUT_SECONDS = 20
MAX_TOKENS = 250

FALLBACK_MODELS = (
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
)

SYSTEM_PROMPT = (
    "You are LimkoBot, the WhatsApp assistant for Limkokwing University in "
    "Sierra Leone (Freetown campus). Answer briefly and helpfully, in WhatsApp "
    "style (short paragraphs, no markdown tables).\n"
    "LANGUAGE RULE: if the student writes Krio (for example: aw, di, mi, yu, "
    "wetin, naw, una, abeg, tenki, kushe), reply ENTIRELY in Sierra Leone Krio. "
    "If the student writes English, reply in English. If mixed, mirror the mix.\n"
    "Krio example - Student: Aw much di fees? Assistant: Di application fee na "
    "USD 100. Tuition de change pan programme ɛn campus, so tɛl mi di programme "
    "we yu want ɛn a go sho yu di exact fee.\n"
    "Known facts: application fee is USD 100; 2026 final exams run 8-19 June; "
    "registration is online through the student portal before semester start; "
    "programmes include diplomas, degrees and postgraduate courses in computing, "
    "design, business, communication and architecture.\n"
    "If you are unsure, say so and offer the menu: 1 = Fees, 2 = Exam schedule, "
    "3 = Registration, 4 = Programmes, 5 = Support. Do not invent fees, dates or "
    "requirements, and do not discuss topics unrelated to the university."
)


def _models() -> list[str]:
    models: list[str] = []
    for model in (settings.GROQ_LLM_MODEL, *FALLBACK_MODELS):
        if model and model not in models:
            models.append(model)
    return models


def answer(question: str, context: str | None = None) -> str | None:
    question = (question or "").strip()
    if not question or not settings.GROQ_API_KEY:
        return None

    user_content = question
    if context:
        user_content = f"Context:\n{context}\n\nStudent question: {question}"

    url = f"{settings.GROQ_BASE_URL}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.GROQ_API_KEY}"}

    for model in _models():
        payload = {
            "model": model,
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
            logger.exception("Groq chat request failed (model=%s)", model)
            continue

        if response.status_code == 404 and "model_not_found" in response.text:
            logger.warning("Groq model unavailable, trying next: %s", model)
            continue

        if response.status_code >= 400:
            logger.warning(
                "Groq chat HTTP %s (model=%s): %s",
                response.status_code,
                model,
                response.text[:300],
            )
            return None

        try:
            choices = response.json().get("choices") or []
            content = (choices[0].get("message") or {}).get("content") or ""
        except Exception:  # noqa: BLE001 - fallback is best-effort
            logger.exception("Groq chat response was not usable (model=%s)", model)
            return None

        cleaned = content.strip()
        if cleaned:
            return cleaned

    return None
