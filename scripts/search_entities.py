#!/usr/bin/env python3
"""
Semantic search for entities using pgvector cosine similarity.

Search the entity database using natural language queries and vector embeddings.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text

from mothra.db.models import CarbonEntity
from mothra.db.session import get_db_context
from mothra.utils.embeddings import generate_embedding
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


async def semantic_search(
    query: str,
    limit: int = 10,
    entity_type: str | None = None,
    min_similarity: float = 0.0,
) -> list[dict]:
    """
    Search entities using semantic similarity.

    Args:
        query: Natural language search query
        limit: Maximum number of results
        entity_type: Filter by entity type (optional)
        min_similarity: Minimum cosine similarity threshold (0-1)

    Returns:
        List of matching entities with similarity scores
    """
    # Generate query embedding
    query_embedding = generate_embedding(query)

    async with get_db_context() as db:
        # Build query with cosine similarity
        # Note: pgvector uses <=> for cosine distance (lower is better)
        # Similarity = 1 - distance
        stmt = select(
            CarbonEntity,
            (1 - CarbonEntity.embedding.cosine_distance(query_embedding)).label("similarity"),
        ).where(
            CarbonEntity.embedding.is_not(None)
        )

        # Filter by entity type if specified
        if entity_type:
            stmt = stmt.where(CarbonEntity.entity_type == entity_type)

        # Order by similarity (highest first) and limit
        stmt = stmt.order_by(text("similarity DESC")).limit(limit)

        result = await db.execute(stmt)
        rows = result.all()

        # Format results
        results = []
        for entity, similarity in rows:
            if similarity >= min_similarity:
                results.append({
                    "entity": entity,
                    "similarity": float(similarity),
                })

        return results


async def search_and_display(
    query: str,
    limit: int = 10,
    entity_type: str | None = None,
    min_similarity: float = 0.0,
    show_details: bool = False,
):
    """Search and display results."""
    print(f"\n{'='*80}")
    print(f"Semantic Search: '{query}'")
    print(f"{'='*80}")
    print(f"Limit: {limit} results")
    if entity_type:
        print(f"Entity type filter: {entity_type}")
    if min_similarity > 0:
        print(f"Minimum similarity: {min_similarity}")
    print()

    results = await semantic_search(
        query=query,
        limit=limit,
        entity_type=entity_type,
        min_similarity=min_similarity,
    )

    if not results:
        print("No results found!")
        return

    print(f"Found {len(results)} results:\n")

    for i, result in enumerate(results, 1):
        entity = result["entity"]
        similarity = result["similarity"]

        print(f"{i}. [{similarity:.3f}] {entity.name}")
        print(f"   Type: {entity.entity_type}")

        if entity.category_hierarchy:
            print(f"   Categories: {' > '.join(entity.category_hierarchy[:3])}")

        if entity.geographic_scope:
            print(f"   Location: {', '.join(entity.geographic_scope[:3])}")

        if show_details:
            if entity.description:
                desc = entity.description[:200] + "..." if len(entity.description) > 200 else entity.description
                print(f"   Description: {desc}")

            if entity.custom_tags:
                print(f"   Tags: {', '.join(entity.custom_tags[:5])}")

        print()

    logger.info(
        "search_complete",
        query=query,
        results_count=len(results),
        top_similarity=results[0]["similarity"] if results else 0,
    )


async def main_async(args):
    """Main async function."""
    await search_and_display(
        query=args.query,
        limit=args.limit,
        entity_type=args.type,
        min_similarity=args.min_similarity,
        show_details=args.details,
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Semantic search for entities using natural language"
    )
    parser.add_argument(
        "query",
        type=str,
        help="Search query (natural language)",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)",
    )
    parser.add_argument(
        "-t", "--type",
        type=str,
        default=None,
        help="Filter by entity type (e.g., emission, process, material)",
    )
    parser.add_argument(
        "-s", "--min-similarity",
        type=float,
        default=0.0,
        help="Minimum similarity threshold 0-1 (default: 0.0)",
    )
    parser.add_argument(
        "-d", "--details",
        action="store_true",
        help="Show detailed information for each result",
    )

    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
