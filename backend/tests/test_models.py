from sqlalchemy.orm import configure_mappers

from app import models  # noqa: F401  (registers every mapper)


def test_mappers_configure_without_missing_relationships():
    """Every relationship back_populates must resolve; a stray name breaks all ORM queries."""
    configure_mappers()

    assert models.User.conversations.property.back_populates == "user"
    assert models.Conversation.user.property.back_populates == "conversations"
    assert models.Conversation.messages.property.back_populates == "conversation"
    assert models.Message.conversation.property.back_populates == "messages"
    assert models.Document.chunks.property.back_populates == "document"
    assert models.Chunk.document.property.back_populates == "chunks"


def test_user_table_has_staff_columns():
    columns = models.User.__table__.columns.keys()
    for name in ("id", "phone", "email", "hashed_password", "role", "is_verified"):
        assert name in columns
