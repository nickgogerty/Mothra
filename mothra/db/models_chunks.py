"""
Document Chunk Model for Large Context Embeddings.

This model stores chunks of large documents with individual embeddings,
enabling semantic search across documents that exceed the embedding model's
context window (512 tokens / ~2000 characters).
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    TIMESTAMP,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from mothra.config import settings
from mothra.db.base import Base


class DocumentChunk(Base):
    """Individual chunk of a carbon entity for embedding."""

    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Reference to parent entity
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carbon_entities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Chunk metadata
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, nullable=False)

    # Chunk content
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False)  # Character count

    # Position in original document
    start_position: Mapped[int] = mapped_column(Integer, nullable=False)
    end_position: Mapped[int] = mapped_column(Integer, nullable=False)

    # Overlap with adjacent chunks
    overlap_before: Mapped[int] = mapped_column(Integer, default=0)
    overlap_after: Mapped[int] = mapped_column(Integer, default=0)

    # Vector embedding for this chunk
    embedding: Mapped[Any] = mapped_column(
        Vector(settings.embedding_dimension), nullable=True
    )

    # Chunk quality/relevance score
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<DocumentChunk(id={self.id}, entity_id={self.entity_id}, "
            f"chunk_index={self.chunk_index}/{self.total_chunks})>"
        )
