"""
Embedding utilities for semantic search using sentence-transformers.

Uses local sentence-transformers models (no API required) for generating
embeddings that are stored in PostgreSQL pgvector columns.
"""

from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from mothra.config import get_settings
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    """
    Get cached sentence transformer model.

    Returns:
        Loaded SentenceTransformer model
    """
    settings = get_settings()
    model_name = settings.embedding_model

    logger.info(
        "embedding_model_loading",
        model=model_name,
        dimension=settings.embedding_dimension,
    )

    model = SentenceTransformer(model_name)

    logger.info(
        "embedding_model_loaded",
        model=model_name,
        max_seq_length=model.max_seq_length,
    )

    return model


def generate_embedding(text: str) -> np.ndarray:
    """
    Generate embedding vector for text.

    Args:
        text: Text to embed

    Returns:
        Embedding vector as numpy array
    """
    if not text or not text.strip():
        # Return zero vector for empty text
        settings = get_settings()
        return np.zeros(settings.embedding_dimension)

    model = get_embedding_model()
    embedding = model.encode(text, normalize_embeddings=True)

    return embedding


def generate_embeddings_batch(texts: list[str], batch_size: int = 32) -> list[np.ndarray]:
    """
    Generate embeddings for multiple texts efficiently.

    Args:
        texts: List of texts to embed
        batch_size: Batch size for encoding

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 100,
    )

    return embeddings.tolist()


def create_searchable_text(entity_dict: dict) -> str:
    """
    Create searchable text from entity dictionary for embedding.

    Combines name, description, and key metadata fields.

    Args:
        entity_dict: Entity dictionary with name, description, etc.

    Returns:
        Combined searchable text
    """
    parts = []

    # Add name (most important)
    if name := entity_dict.get("name"):
        parts.append(name)

    # Add description
    if desc := entity_dict.get("description"):
        parts.append(desc)

    # Add entity type
    if entity_type := entity_dict.get("entity_type"):
        parts.append(f"Type: {entity_type}")

    # Add category hierarchy
    if categories := entity_dict.get("category_hierarchy"):
        if isinstance(categories, list):
            parts.append("Categories: " + " > ".join(categories))

    # Add custom tags
    if tags := entity_dict.get("custom_tags"):
        if isinstance(tags, list):
            parts.append("Tags: " + ", ".join(tags[:5]))  # Limit to first 5 tags

    # Add geographic scope
    if geo := entity_dict.get("geographic_scope"):
        if isinstance(geo, list):
            parts.append("Location: " + ", ".join(geo))

    return " | ".join(parts)
