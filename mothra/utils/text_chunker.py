"""
Text Chunker for Large Documents.

Intelligently splits large text into chunks that fit within the embedding model's
context window while preserving semantic coherence through overlapping.
"""

from typing import Any
from uuid import UUID

from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class TextChunker:
    """Chunk large text for embedding."""

    def __init__(
        self,
        chunk_size: int = 1500,  # Characters per chunk (~375 tokens)
        overlap: int = 200,  # Overlap between chunks
        max_seq_length: int = 512,  # Model's max tokens
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            max_seq_length: Maximum sequence length for embedding model
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunk_overlap = overlap  # Alias for consistency
        self.max_seq_length = max_seq_length

        # Rough estimate: 4 characters per token
        self.chars_per_token = 4
        self.max_chunk_chars = max_seq_length * self.chars_per_token

        # Ensure chunk_size doesn't exceed model limits
        if chunk_size > self.max_chunk_chars:
            logger.warning(
                "chunk_size_exceeds_limit",
                chunk_size=chunk_size,
                max_chars=self.max_chunk_chars,
            )
            self.chunk_size = self.max_chunk_chars

    def chunk_text(self, text: str, entity_id: UUID | None = None) -> list[dict[str, Any]]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            entity_id: Optional entity ID for logging

        Returns:
            List of chunk dictionaries with metadata
        """
        if not text or len(text) == 0:
            return []

        text_length = len(text)

        # If text fits in one chunk, return it as-is
        if text_length <= self.chunk_size:
            return [
                {
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "chunk_text": text,
                    "chunk_size": text_length,
                    "start_position": 0,
                    "end_position": text_length,
                    "overlap_before": 0,
                    "overlap_after": 0,
                }
            ]

        # Split into chunks with overlap
        chunks = []
        start = 0
        chunk_index = 0

        while start < text_length:
            # Calculate end position
            end = min(start + self.chunk_size, text_length)

            # Try to break at sentence boundary if possible
            if end < text_length:
                # Look for sentence endings within last 20% of chunk
                search_start = max(start, end - int(self.chunk_size * 0.2))
                sentence_ends = ['.', '!', '?', '\n\n']

                best_break = end
                for sent_end in sentence_ends:
                    pos = text.rfind(sent_end, search_start, end)
                    if pos != -1 and pos > search_start:
                        best_break = pos + 1
                        break

                end = best_break

            # Extract chunk text
            chunk_text = text[start:end].strip()

            # Calculate overlaps
            overlap_before = self.overlap if start > 0 else 0
            overlap_after = self.overlap if end < text_length else 0

            # Include overlap from previous chunk
            actual_start = max(0, start - overlap_before)
            # Include overlap for next chunk
            actual_end = min(text_length, end + overlap_after)

            # Get text with overlap
            chunk_with_overlap = text[actual_start:actual_end].strip()

            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "chunk_text": chunk_with_overlap,
                    "chunk_size": len(chunk_with_overlap),
                    "start_position": actual_start,
                    "end_position": actual_end,
                    "overlap_before": overlap_before if chunk_index > 0 else 0,
                    "overlap_after": overlap_after,
                }
            )

            # Move to next chunk (minus overlap)
            start = end
            chunk_index += 1

        # Update total_chunks for all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["total_chunks"] = total_chunks

        logger.debug(
            "text_chunked",
            entity_id=str(entity_id) if entity_id else None,
            text_length=text_length,
            total_chunks=total_chunks,
            avg_chunk_size=text_length // total_chunks if total_chunks > 0 else 0,
        )

        return chunks

    def should_chunk(self, text: str) -> bool:
        """
        Determine if text needs chunking.

        Args:
            text: Text to check

        Returns:
            True if text exceeds chunk_size
        """
        return len(text) > self.chunk_size

    def estimate_chunks(self, text: str) -> int:
        """
        Estimate number of chunks needed.

        Args:
            text: Text to estimate

        Returns:
            Estimated number of chunks
        """
        if not text:
            return 0

        text_length = len(text)

        if text_length <= self.chunk_size:
            return 1

        # Account for overlap reducing effective chunk size
        effective_chunk_size = self.chunk_size - self.overlap
        return (text_length + effective_chunk_size - 1) // effective_chunk_size


def create_searchable_text_for_chunking(entity_data: dict[str, Any]) -> str:
    """
    Create comprehensive searchable text from entity data for chunking.

    Includes all available fields to maximize semantic context.

    Args:
        entity_data: Entity data dictionary

    Returns:
        Formatted text string
    """
    parts = []

    # Core fields
    if "name" in entity_data:
        parts.append(f"Name: {entity_data['name']}")

    if "description" in entity_data:
        parts.append(f"Description: {entity_data['description']}")

    if "entity_type" in entity_data:
        parts.append(f"Type: {entity_data['entity_type']}")

    # Category and taxonomy
    if "category_hierarchy" in entity_data and entity_data["category_hierarchy"]:
        categories = " > ".join(entity_data["category_hierarchy"])
        parts.append(f"Category: {categories}")

    # Geographic scope
    if "geographic_scope" in entity_data and entity_data["geographic_scope"]:
        regions = ", ".join(entity_data["geographic_scope"])
        parts.append(f"Geographic Scope: {regions}")

    # Tags
    if "custom_tags" in entity_data and entity_data["custom_tags"]:
        tags = ", ".join(entity_data["custom_tags"])
        parts.append(f"Tags: {tags}")

    # Additional metadata
    if "extra_metadata" in entity_data and entity_data["extra_metadata"]:
        metadata = entity_data["extra_metadata"]

        # Add selected metadata fields
        metadata_parts = []
        for key, value in metadata.items():
            if key in [
                "activity",
                "fuel_material",
                "sector",
                "industry_type",
                "manufacturer",
                "product_name",
            ]:
                metadata_parts.append(f"{key}: {value}")

        if metadata_parts:
            parts.append("Metadata: " + ", ".join(metadata_parts))

    # Raw data if available (for very detailed entities)
    if "raw_data" in entity_data and entity_data["raw_data"]:
        # Include limited raw data fields
        raw = entity_data["raw_data"]
        if isinstance(raw, dict):
            raw_parts = []
            for key, value in list(raw.items())[:10]:  # Limit to 10 fields
                if isinstance(value, (str, int, float)):
                    raw_parts.append(f"{key}: {value}")

            if raw_parts:
                parts.append("Additional Details: " + ", ".join(raw_parts))

    return "\n".join(parts)
