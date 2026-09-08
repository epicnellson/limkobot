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
        "I'm still learning about Limkokwing University. "
        "Please check back soon or ask again later."
    )