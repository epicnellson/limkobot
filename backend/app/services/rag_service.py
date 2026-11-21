import logging

logger = logging.getLogger(__name__)


def answer(query: str, conversation_id: str | None = None) -> str:
    """Generate a bot answer.

    Phase 3 will replace this stub with the hybrid RAG pipeline:
    vector + keyword retrieval over knowledge-base chunks, then LLM
    answer generation with citations.
    """
    logger.info("RAG stub answer for query=%r conversation=%s", query, conversation_id)
    return (
        "I'm still learning about Limkokwing University, so I may not have that answer yet.\n\n"
        "Reply 1 = Fees, 2 = Exam schedule, 3 = Registration, 4 = Programmes, "
        "5 = Support, or type MENU. A staff member will follow up on anything else."
    )
