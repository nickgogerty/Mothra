"""
Data source endpoints
Clear provenance information (Tufte's data credibility principle)
"""

from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from mothra.db.session import get_async_session
from mothra.db.models import DataSource, CrawlLog

router = APIRouter()


class DataSourceSummary(BaseModel):
    """Data source summary."""

    id: str
    name: str
    url: str
    source_type: str
    category: str
    priority: str
    status: str
    last_crawled: Optional[str]
    last_successful_crawl: Optional[str]
    error_count: int
    update_frequency: Optional[str]
    estimated_size_gb: Optional[float]


class CrawlLogDetail(BaseModel):
    """Crawl log details."""

    id: str
    started_at: str
    completed_at: Optional[str]
    status: str
    records_found: int
    records_processed: int
    records_inserted: int
    records_updated: int
    records_failed: int
    duration_seconds: Optional[float]
    error_message: Optional[str]


class DataSourceDetail(BaseModel):
    """Detailed data source information."""

    id: str
    name: str
    url: str
    source_type: str
    category: str
    priority: str
    access_method: str
    auth_required: bool
    rate_limit: Optional[int]
    update_frequency: Optional[str]
    data_format: Optional[str]
    estimated_size_gb: Optional[float]
    status: str
    last_crawled: Optional[str]
    last_successful_crawl: Optional[str]
    error_count: int
    recent_crawls: list[CrawlLogDetail]
    created_at: str
    updated_at: str


class SourcesResponse(BaseModel):
    """Paginated sources response."""

    sources: list[DataSourceSummary]
    total: int
    page: int
    page_size: int


@router.get("/sources", response_model=SourcesResponse)
async def list_sources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
):
    """
    List data sources with status information.

    Provides transparency about data provenance and quality.
    """
    try:
        async with get_async_session() as session:
            # Build query
            conditions = []
            if status:
                conditions.append(DataSource.status == status)
            if category:
                conditions.append(DataSource.category == category)
            if priority:
                conditions.append(DataSource.priority == priority)

            # Count total
            count_stmt = select(func.count()).select_from(DataSource)
            if conditions:
                from sqlalchemy import and_
                count_stmt = count_stmt.where(and_(*conditions))

            total_result = await session.execute(count_stmt)
            total = total_result.scalar()

            # Get paginated results
            offset = (page - 1) * page_size
            stmt = select(DataSource)

            if conditions:
                from sqlalchemy import and_
                stmt = stmt.where(and_(*conditions))

            stmt = stmt.order_by(DataSource.priority, DataSource.name).offset(offset).limit(page_size)

            result = await session.execute(stmt)
            sources = result.scalars().all()

            # Transform to response
            source_summaries = [
                DataSourceSummary(
                    id=str(source.id),
                    name=source.name,
                    url=source.url,
                    source_type=source.source_type,
                    category=source.category,
                    priority=source.priority,
                    status=source.status,
                    last_crawled=source.last_crawled.isoformat() if source.last_crawled else None,
                    last_successful_crawl=(
                        source.last_successful_crawl.isoformat()
                        if source.last_successful_crawl
                        else None
                    ),
                    error_count=source.error_count,
                    update_frequency=source.update_frequency,
                    estimated_size_gb=source.estimated_size_gb,
                )
                for source in sources
            ]

            return SourcesResponse(
                sources=source_summaries,
                total=total,
                page=page,
                page_size=page_size,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve sources: {str(e)}",
        )


@router.get("/sources/{source_id}", response_model=DataSourceDetail)
async def get_source(source_id: UUID):
    """
    Get detailed information about a data source.

    Includes crawl history and performance metrics.
    """
    try:
        async with get_async_session() as session:
            # Get source
            stmt = select(DataSource).where(DataSource.id == source_id)
            result = await session.execute(stmt)
            source = result.scalar_one_or_none()

            if not source:
                raise HTTPException(
                    status_code=404,
                    detail=f"Source {source_id} not found",
                )

            # Get recent crawl logs
            crawl_stmt = (
                select(CrawlLog)
                .where(CrawlLog.source_id == source_id)
                .order_by(CrawlLog.started_at.desc())
                .limit(10)
            )
            crawl_result = await session.execute(crawl_stmt)
            crawls = crawl_result.scalars().all()

            # Transform crawl logs
            crawl_details = [
                CrawlLogDetail(
                    id=str(crawl.id),
                    started_at=crawl.started_at.isoformat(),
                    completed_at=crawl.completed_at.isoformat() if crawl.completed_at else None,
                    status=crawl.status,
                    records_found=crawl.records_found,
                    records_processed=crawl.records_processed,
                    records_inserted=crawl.records_inserted,
                    records_updated=crawl.records_updated,
                    records_failed=crawl.records_failed,
                    duration_seconds=crawl.duration_seconds,
                    error_message=crawl.error_message,
                )
                for crawl in crawls
            ]

            return DataSourceDetail(
                id=str(source.id),
                name=source.name,
                url=source.url,
                source_type=source.source_type,
                category=source.category,
                priority=source.priority,
                access_method=source.access_method,
                auth_required=source.auth_required,
                rate_limit=source.rate_limit,
                update_frequency=source.update_frequency,
                data_format=source.data_format,
                estimated_size_gb=source.estimated_size_gb,
                status=source.status,
                last_crawled=source.last_crawled.isoformat() if source.last_crawled else None,
                last_successful_crawl=(
                    source.last_successful_crawl.isoformat()
                    if source.last_successful_crawl
                    else None
                ),
                error_count=source.error_count,
                recent_crawls=crawl_details,
                created_at=source.created_at.isoformat(),
                updated_at=source.updated_at.isoformat(),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve source: {str(e)}",
        )
