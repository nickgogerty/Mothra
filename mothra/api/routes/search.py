"""
Semantic search endpoints
Following Nielsen's usability heuristics: provide clear feedback and error messages
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from mothra.db.session import get_async_session
from mothra.db.models import CarbonEntity, EmissionFactor
from mothra.agents.embedding.vector_manager import VectorManager

router = APIRouter()


class SearchRequest(BaseModel):
    """Search request with semantic query."""

    query: str = Field(..., min_length=1, description="Search query text")
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    similarity_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity score")


class SearchResult(BaseModel):
    """Individual search result."""

    id: str
    name: str
    entity_type: str
    description: Optional[str]
    quality_score: Optional[float]
    confidence_level: Optional[float]
    similarity: float
    category: Optional[list[str]]
    geographic_scope: Optional[list[str]]


class SearchResponse(BaseModel):
    """Search response with results and metadata."""

    query: str
    results: list[SearchResult]
    total: int
    execution_time_ms: float


@router.post("/search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search across carbon entities.

    Uses vector embeddings for intelligent, meaning-based search.
    Results are ranked by semantic similarity.
    """
    import time
    start_time = time.time()

    try:
        # Initialize vector manager
        vector_manager = VectorManager()

        # Perform semantic search
        results = await vector_manager.semantic_search(
            query_text=request.query,
            entity_type=request.entity_type,
            similarity_threshold=request.similarity_threshold,
            limit=request.limit,
        )

        # Transform to response format
        search_results = [
            SearchResult(
                id=str(result["id"]),
                name=result["name"],
                entity_type=result["entity_type"],
                description=result.get("description"),
                quality_score=result.get("quality_score"),
                confidence_level=result.get("confidence_level"),
                similarity=result.get("similarity", 0.0),
                category=result.get("category_hierarchy"),
                geographic_scope=result.get("geographic_scope"),
            )
            for result in results
        ]

        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        return SearchResponse(
            query=request.query,
            results=search_results,
            total=len(search_results),
            execution_time_ms=round(execution_time, 2),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )


@router.get("/search/suggestions")
async def search_suggestions(
    q: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(5, ge=1, le=20),
):
    """
    Get search suggestions for autocomplete.

    Provides instant feedback as users type (Nielsen's visibility heuristic).
    """
    try:
        async with get_async_session() as session:
            # Simple text-based suggestions using ILIKE
            stmt = (
                select(CarbonEntity.name, CarbonEntity.entity_type)
                .where(
                    or_(
                        CarbonEntity.name.ilike(f"%{q}%"),
                        CarbonEntity.description.ilike(f"%{q}%"),
                    )
                )
                .limit(limit)
            )

            result = await session.execute(stmt)
            suggestions = [
                {"name": row.name, "type": row.entity_type}
                for row in result.all()
            ]

            return {"suggestions": suggestions, "query": q}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get suggestions: {str(e)}",
        )
