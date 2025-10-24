"""
SQLAlchemy models for MOTHRA carbon database.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    CheckConstraint,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, DATERANGE, UUID
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from mothra.config import settings
from mothra.db.base import Base


class DataSource(Base):
    """Catalog of carbon data sources."""

    __tablename__ = "data_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # api, web_scrape, document, stream
    category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # government, standards, research, commercial
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="medium"
    )  # critical, high, medium, low

    # Access configuration
    access_method: Mapped[str] = mapped_column(String(50), nullable=False)  # rest, graphql, scrape
    auth_required: Mapped[bool] = mapped_column(default=False)
    rate_limit: Mapped[int] = mapped_column(Integer, nullable=True)  # requests per minute

    # Metadata
    update_frequency: Mapped[str] = mapped_column(
        String(50), nullable=True
    )  # realtime, hourly, daily, weekly, monthly
    data_format: Mapped[str] = mapped_column(String(50), nullable=True)  # json, xml, csv, pdf
    estimated_size_gb: Mapped[float] = mapped_column(Float, nullable=True)
    schema_type: Mapped[str] = mapped_column(String(100), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="discovered"
    )  # discovered, validated, active, inactive, failed
    last_crawled: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_successful_crawl: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True), nullable=True
    )
    error_count: Mapped[int] = mapped_column(Integer, default=0)

    # Additional metadata
    metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_data_sources_status", "status"),
        Index("idx_data_sources_priority", "priority"),
        Index("idx_data_sources_category", "category"),
    )


class CarbonEntity(Base):
    """Core carbon entity - processes, materials, products, services."""

    __tablename__ = "carbon_entities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_uuid: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # Reference to DataSource

    entity_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # process, material, product, service, energy
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Taxonomy
    category_hierarchy: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    isic_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    unspsc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    naics_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    custom_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Geographic and temporal scope
    geographic_scope: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    temporal_validity: Mapped[Any] = mapped_column(DATERANGE, nullable=True)

    # Data quality
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )  # pending, validated, rejected

    # Raw data and metadata
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)
    metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Vector embedding for semantic search
    embedding: Mapped[Any] = mapped_column(
        Vector(settings.embedding_dimension), nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_carbon_entities_type", "entity_type"),
        Index("idx_carbon_entities_source", "source_id"),
        Index("idx_carbon_entities_validation", "validation_status"),
        Index("idx_carbon_entities_quality", "quality_score"),
        Index(
            "idx_carbon_entities_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        CheckConstraint("quality_score >= 0 AND quality_score <= 1", name="quality_score_range"),
        CheckConstraint(
            "confidence_level >= 0 AND confidence_level <= 1", name="confidence_level_range"
        ),
    )


class EmissionFactor(Base):
    """Emission factors associated with carbon entities."""

    __tablename__ = "emission_factors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Emission value
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(100), nullable=False)  # kgCO2e/unit

    # Scope and lifecycle
    scope: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1, 2, or 3
    lifecycle_stage: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # cradle, gate, grave, use

    # Calculation method and standard
    calculation_method: Mapped[str | None] = mapped_column(Text, nullable=True)
    accounting_standard: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # ISO14040, PAS2050, GHG_Protocol

    # Uncertainty
    uncertainty_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    uncertainty_distribution: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # normal, lognormal, uniform

    # Geographic and temporal scope
    geographic_scope: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)
    temporal_scope: Mapped[Any] = mapped_column(DATERANGE, nullable=True)

    # Quality
    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_quality_flags: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Vector embedding
    embedding: Mapped[Any] = mapped_column(
        Vector(settings.embedding_dimension), nullable=True
    )

    # Metadata
    metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_emission_factors_entity", "entity_id"),
        Index("idx_emission_factors_scope", "scope"),
        Index("idx_emission_factors_lifecycle", "lifecycle_stage"),
        Index("idx_emission_factors_quality", "quality_score"),
        Index(
            "idx_emission_factors_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        CheckConstraint("value >= 0", name="emission_value_positive"),
        CheckConstraint("scope IN (1, 2, 3)", name="valid_scope"),
        CheckConstraint("quality_score >= 0 AND quality_score <= 1", name="ef_quality_score_range"),
    )


class ProcessRelationship(Base):
    """Relationships between carbon entities (parent/child processes, substitutes)."""

    __tablename__ = "process_relationships"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    relationship_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # parent, child, substitute, equivalent

    # Relationship metadata
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)  # For weighted relationships
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        Index("idx_process_relationships_source", "source_entity_id"),
        Index("idx_process_relationships_target", "target_entity_id"),
        Index("idx_process_relationships_type", "relationship_type"),
    )


class CrawlLog(Base):
    """Log of crawling activities."""

    __tablename__ = "crawl_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Crawl details
    started_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # running, completed, failed, partial

    # Results
    records_found: Mapped[int] = mapped_column(Integer, default=0)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True)

    # Performance metrics
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_size_mb: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Metadata
    metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    __table_args__ = (
        Index("idx_crawl_logs_source", "source_id"),
        Index("idx_crawl_logs_status", "status"),
        Index("idx_crawl_logs_started", "started_at"),
    )
