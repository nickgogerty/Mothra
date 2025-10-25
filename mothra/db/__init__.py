"""Database models and utilities for MOTHRA."""

from mothra.db.session import get_db, init_db
from mothra.db.base import Base

# Import all models to register them with Base metadata
from mothra.db.models import (  # noqa: F401
    CarbonEntity,
    CrawlLog,
    DataSource,
    EmissionFactor,
    ProcessRelationship,
)
from mothra.db.models_chunks import DocumentChunk  # noqa: F401

__all__ = ["Base", "get_db", "init_db", "DocumentChunk"]
