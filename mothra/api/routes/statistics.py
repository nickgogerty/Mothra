"""
Statistics and analytics endpoints
Following Tufte's principles: data density, clarity, precision
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from mothra.db.session import get_async_session
from mothra.db.models import CarbonEntity, EmissionFactor, DataSource, CrawlLog

router = APIRouter()


class QualityDistribution(BaseModel):
    """Quality score distribution."""

    range: str
    count: int
    percentage: float


class EntityTypeStats(BaseModel):
    """Statistics by entity type."""

    entity_type: str
    count: int
    avg_quality: float
    validated: int
    pending: int


class SourceStats(BaseModel):
    """Statistics by source category."""

    category: str
    active_sources: int
    total_entities: int
    avg_quality: float
    last_updated: str


class ScopeDistribution(BaseModel):
    """GHG scope distribution."""

    scope: int
    count: int
    percentage: float


class DatabaseStats(BaseModel):
    """Overall database statistics."""

    total_entities: int
    total_emission_factors: int
    total_sources: int
    active_sources: int
    validated_entities: int
    avg_quality_score: float
    entity_types: int
    geographic_regions: int
    last_update: str


class DetailedStatistics(BaseModel):
    """Comprehensive statistics response."""

    overview: DatabaseStats
    quality_distribution: list[QualityDistribution]
    entity_type_breakdown: list[EntityTypeStats]
    source_breakdown: list[SourceStats]
    scope_distribution: list[ScopeDistribution]


@router.get("/statistics", response_model=DetailedStatistics)
async def get_statistics():
    """
    Get comprehensive database statistics.

    Provides high-density, informative overview of system state.
    Follows Tufte's principles: show data variation, not data redundancy.
    """
    try:
        async with get_async_session() as session:
            # === Overview Statistics ===

            # Total entities
            total_entities_stmt = select(func.count()).select_from(CarbonEntity)
            total_entities = (await session.execute(total_entities_stmt)).scalar()

            # Total emission factors
            total_ef_stmt = select(func.count()).select_from(EmissionFactor)
            total_ef = (await session.execute(total_ef_stmt)).scalar()

            # Total and active sources
            total_sources_stmt = select(func.count()).select_from(DataSource)
            total_sources = (await session.execute(total_sources_stmt)).scalar()

            active_sources_stmt = select(func.count()).select_from(DataSource).where(
                DataSource.status == "active"
            )
            active_sources = (await session.execute(active_sources_stmt)).scalar()

            # Validated entities
            validated_stmt = select(func.count()).select_from(CarbonEntity).where(
                CarbonEntity.validation_status == "validated"
            )
            validated = (await session.execute(validated_stmt)).scalar()

            # Average quality score
            avg_quality_stmt = select(func.avg(CarbonEntity.quality_score)).where(
                CarbonEntity.quality_score.isnot(None)
            )
            avg_quality = (await session.execute(avg_quality_stmt)).scalar() or 0.0

            # Distinct entity types
            entity_types_stmt = select(func.count(func.distinct(CarbonEntity.entity_type)))
            entity_types_count = (await session.execute(entity_types_stmt)).scalar()

            # Distinct geographic regions (using subquery to avoid nested aggregate error)
            from sqlalchemy import text
            geo_result = await session.execute(
                text("SELECT COUNT(DISTINCT region) FROM (SELECT unnest(geographic_scope) as region FROM carbon_entities) as regions")
            )
            geo_count = geo_result.scalar() or 0

            # Last update from crawl logs
            last_update_stmt = select(func.max(CrawlLog.completed_at))
            last_update = (await session.execute(last_update_stmt)).scalar()

            overview = DatabaseStats(
                total_entities=total_entities,
                total_emission_factors=total_ef,
                total_sources=total_sources,
                active_sources=active_sources,
                validated_entities=validated,
                avg_quality_score=round(avg_quality, 3),
                entity_types=entity_types_count,
                geographic_regions=geo_count,
                last_update=last_update.isoformat() if last_update else "N/A",
            )

            # === Quality Distribution ===
            quality_ranges = [
                ("0.0-0.2", 0.0, 0.2),
                ("0.2-0.4", 0.2, 0.4),
                ("0.4-0.6", 0.4, 0.6),
                ("0.6-0.8", 0.6, 0.8),
                ("0.8-1.0", 0.8, 1.0),
            ]

            quality_distribution = []
            for range_label, min_val, max_val in quality_ranges:
                count_stmt = select(func.count()).select_from(CarbonEntity).where(
                    and_(
                        CarbonEntity.quality_score >= min_val,
                        CarbonEntity.quality_score < max_val if max_val < 1.0 else CarbonEntity.quality_score <= max_val,
                        CarbonEntity.quality_score.isnot(None),
                    )
                )
                count = (await session.execute(count_stmt)).scalar()
                percentage = (count / total_entities * 100) if total_entities > 0 else 0

                quality_distribution.append(
                    QualityDistribution(
                        range=range_label,
                        count=count,
                        percentage=round(percentage, 1),
                    )
                )

            # === Entity Type Breakdown ===
            entity_type_stmt = select(
                CarbonEntity.entity_type,
                func.count().label("count"),
                func.avg(CarbonEntity.quality_score).label("avg_quality"),
                func.sum(case((CarbonEntity.validation_status == "validated", 1), else_=0)).label("validated"),
                func.sum(case((CarbonEntity.validation_status == "pending", 1), else_=0)).label("pending"),
            ).group_by(CarbonEntity.entity_type).order_by(func.count().desc())

            entity_type_result = await session.execute(entity_type_stmt)
            entity_type_breakdown = [
                EntityTypeStats(
                    entity_type=row.entity_type,
                    count=row.count,
                    avg_quality=round(row.avg_quality or 0.0, 3),
                    validated=row.validated,
                    pending=row.pending,
                )
                for row in entity_type_result.all()
            ]

            # === Source Breakdown ===
            # This is a simplified version - would need JOIN for exact entity counts
            source_category_stmt = select(
                DataSource.category,
                func.count().label("active_sources"),
            ).where(DataSource.status == "active").group_by(DataSource.category)

            source_result = await session.execute(source_category_stmt)
            source_breakdown = [
                SourceStats(
                    category=row.category,
                    active_sources=row.active_sources,
                    total_entities=0,  # Would require JOIN with entities
                    avg_quality=0.0,   # Would require JOIN with entities
                    last_updated="N/A",  # Simplified
                )
                for row in source_result.all()
            ]

            # === Scope Distribution ===
            scope_stmt = select(
                EmissionFactor.scope,
                func.count().label("count"),
            ).where(EmissionFactor.scope.isnot(None)).group_by(EmissionFactor.scope).order_by(EmissionFactor.scope)

            scope_result = await session.execute(scope_stmt)
            total_scoped = sum(row.count for row in scope_result.all())

            # Re-execute for percentages
            scope_result = await session.execute(scope_stmt)
            scope_distribution = [
                ScopeDistribution(
                    scope=row.scope,
                    count=row.count,
                    percentage=round((row.count / total_scoped * 100) if total_scoped > 0 else 0, 1),
                )
                for row in scope_result.all()
            ]

            return DetailedStatistics(
                overview=overview,
                quality_distribution=quality_distribution,
                entity_type_breakdown=entity_type_breakdown,
                source_breakdown=source_breakdown,
                scope_distribution=scope_distribution,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve statistics: {str(e)}",
        )


@router.get("/statistics/summary")
async def get_summary():
    """
    Get quick summary statistics.

    Minimal, high-information density display.
    """
    try:
        async with get_async_session() as session:
            # Quick counts
            entities = (await session.execute(select(func.count()).select_from(CarbonEntity))).scalar()
            sources = (await session.execute(select(func.count()).select_from(DataSource))).scalar()
            emission_factors = (await session.execute(select(func.count()).select_from(EmissionFactor))).scalar()

            return {
                "entities": entities,
                "sources": sources,
                "emission_factors": emission_factors,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve summary: {str(e)}",
        )
