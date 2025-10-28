"""
Carbon entity endpoints
Designed for data clarity (Tufte) and usability (Nielsen)
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from mothra.db.session import get_async_session
from mothra.db.models import CarbonEntity, EmissionFactor

router = APIRouter()


class EmissionFactorDetail(BaseModel):
    """Emission factor details."""

    id: str
    value: float
    unit: str
    scope: Optional[int]
    lifecycle_stage: Optional[str]
    accounting_standard: Optional[str]
    uncertainty_min: Optional[float]
    uncertainty_max: Optional[float]
    quality_score: Optional[float]
    geographic_scope: Optional[list[str]]


class EntityDetail(BaseModel):
    """Detailed entity information."""

    id: str
    name: str
    entity_type: str
    description: Optional[str]
    category_hierarchy: Optional[list[str]]
    geographic_scope: Optional[list[str]]
    quality_score: Optional[float]
    confidence_level: Optional[float]
    validation_status: str
    source_id: str
    emission_factors: list[EmissionFactorDetail]
    custom_tags: list[str]
    created_at: str
    updated_at: str


class EntitySummary(BaseModel):
    """Minimal entity information for lists."""

    id: str
    name: str
    entity_type: str
    quality_score: Optional[float]
    validation_status: str
    geographic_scope: Optional[list[str]]


class EntitiesResponse(BaseModel):
    """Paginated entities response."""

    entities: list[EntitySummary]
    total: int
    page: int
    page_size: int
    has_next: bool


@router.get("/entities", response_model=EntitiesResponse)
async def list_entities(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    validation_status: Optional[str] = Query(None, description="Filter by validation status"),
    min_quality: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum quality score"),
    geographic_scope: Optional[str] = Query(None, description="Filter by geographic scope"),
):
    """
    List carbon entities with filtering and pagination.

    Designed for efficient data browsing with clear status indicators.
    """
    try:
        async with get_async_session() as session:
            # Build query with filters
            conditions = []

            if entity_type:
                conditions.append(CarbonEntity.entity_type == entity_type)

            if validation_status:
                conditions.append(CarbonEntity.validation_status == validation_status)

            if min_quality is not None:
                conditions.append(CarbonEntity.quality_score >= min_quality)

            if geographic_scope:
                conditions.append(CarbonEntity.geographic_scope.contains([geographic_scope]))

            # Count total
            count_stmt = select(func.count()).select_from(CarbonEntity)
            if conditions:
                count_stmt = count_stmt.where(and_(*conditions))

            total_result = await session.execute(count_stmt)
            total = total_result.scalar()

            # Get paginated results
            offset = (page - 1) * page_size
            stmt = select(CarbonEntity)

            if conditions:
                stmt = stmt.where(and_(*conditions))

            stmt = (
                stmt.order_by(CarbonEntity.quality_score.desc().nullslast())
                .offset(offset)
                .limit(page_size)
            )

            result = await session.execute(stmt)
            entities = result.scalars().all()

            # Transform to response
            entity_summaries = [
                EntitySummary(
                    id=str(entity.id),
                    name=entity.name,
                    entity_type=entity.entity_type,
                    quality_score=entity.quality_score,
                    validation_status=entity.validation_status,
                    geographic_scope=entity.geographic_scope,
                )
                for entity in entities
            ]

            has_next = (offset + page_size) < total

            return EntitiesResponse(
                entities=entity_summaries,
                total=total,
                page=page,
                page_size=page_size,
                has_next=has_next,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve entities: {str(e)}",
        )


@router.get("/entities/{entity_id}", response_model=EntityDetail)
async def get_entity(entity_id: UUID):
    """
    Get detailed information about a specific entity.

    Includes all emission factors and relationships.
    """
    try:
        async with get_async_session() as session:
            # Get entity
            stmt = select(CarbonEntity).where(CarbonEntity.id == entity_id)
            result = await session.execute(stmt)
            entity = result.scalar_one_or_none()

            if not entity:
                raise HTTPException(
                    status_code=404,
                    detail=f"Entity {entity_id} not found",
                )

            # Get associated emission factors
            ef_stmt = select(EmissionFactor).where(EmissionFactor.entity_id == entity_id)
            ef_result = await session.execute(ef_stmt)
            emission_factors = ef_result.scalars().all()

            # Transform emission factors
            ef_details = [
                EmissionFactorDetail(
                    id=str(ef.id),
                    value=ef.value,
                    unit=ef.unit,
                    scope=ef.scope,
                    lifecycle_stage=ef.lifecycle_stage,
                    accounting_standard=ef.accounting_standard,
                    uncertainty_min=ef.uncertainty_min,
                    uncertainty_max=ef.uncertainty_max,
                    quality_score=ef.quality_score,
                    geographic_scope=ef.geographic_scope,
                )
                for ef in emission_factors
            ]

            return EntityDetail(
                id=str(entity.id),
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description,
                category_hierarchy=entity.category_hierarchy,
                geographic_scope=entity.geographic_scope,
                quality_score=entity.quality_score,
                confidence_level=entity.confidence_level,
                validation_status=entity.validation_status,
                source_id=entity.source_id,
                emission_factors=ef_details,
                custom_tags=entity.custom_tags or [],
                created_at=entity.created_at.isoformat(),
                updated_at=entity.updated_at.isoformat(),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve entity: {str(e)}",
        )


@router.get("/entity-types")
async def get_entity_types():
    """
    Get list of available entity types.

    Helps users understand system vocabulary (Nielsen's match between system and real world).
    """
    try:
        async with get_async_session() as session:
            stmt = select(
                CarbonEntity.entity_type,
                func.count().label("count")
            ).group_by(CarbonEntity.entity_type).order_by(func.count().desc())

            result = await session.execute(stmt)
            types = [
                {"type": row.entity_type, "count": row.count}
                for row in result.all()
            ]

            return {"entity_types": types}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve entity types: {str(e)}",
        )
