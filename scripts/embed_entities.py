#!/usr/bin/env python3
"""
Generate embeddings for all entities in the database.

This script processes entities in batches and generates embeddings
for semantic search using local sentence-transformers models.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, update

from mothra.db.models import CarbonEntity
from mothra.db.session import get_db_context
from mothra.utils.embeddings import generate_embeddings_batch, create_searchable_text
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


async def embed_entities(
    batch_size: int = 100,
    limit: int | None = None,
    only_missing: bool = True,
):
    """
    Generate embeddings for entities.

    Args:
        batch_size: Number of entities to process per batch
        limit: Maximum number of entities to process (None = all)
        only_missing: Only process entities without embeddings
    """
    async with get_db_context() as db:
        # Count entities to process
        if only_missing:
            stmt = select(func.count(CarbonEntity.id)).where(
                CarbonEntity.embedding.is_(None)
            )
        else:
            stmt = select(func.count(CarbonEntity.id))

        result = await db.execute(stmt)
        total_count = result.scalar()

        if limit:
            total_count = min(total_count, limit)

        logger.info(
            "embedding_start",
            total_entities=total_count,
            batch_size=batch_size,
            only_missing=only_missing,
        )

    print(f"\n{'='*60}")
    print(f"Embedding Generation")
    print(f"{'='*60}")
    print(f"Total entities to process: {total_count:,}")
    print(f"Batch size: {batch_size}")
    print(f"Only missing: {only_missing}")
    print()

    if total_count == 0:
        print("No entities to process!")
        return

    processed = 0
    failed = 0

    while processed < total_count:
        async with get_db_context() as db:
            # Fetch batch of entities
            if only_missing:
                stmt = (
                    select(CarbonEntity)
                    .where(CarbonEntity.embedding.is_(None))
                    .limit(batch_size)
                )
            else:
                stmt = select(CarbonEntity).offset(processed).limit(batch_size)

            result = await db.execute(stmt)
            entities = result.scalars().all()

            if not entities:
                break

            # Create searchable text for each entity
            texts = []
            entity_ids = []

            for entity in entities:
                # Build entity dict for searchable text
                entity_dict = {
                    "name": entity.name,
                    "description": entity.description,
                    "entity_type": entity.entity_type,
                    "category_hierarchy": entity.category_hierarchy,
                    "custom_tags": entity.custom_tags,
                    "geographic_scope": entity.geographic_scope,
                }

                searchable = create_searchable_text(entity_dict)
                texts.append(searchable)
                entity_ids.append(entity.id)

            # Generate embeddings in batch
            try:
                logger.info(
                    "generating_embeddings",
                    batch_count=len(texts),
                    batch_start=processed,
                )

                embeddings = generate_embeddings_batch(texts, batch_size=32)

                # Update entities with embeddings
                for entity_id, embedding in zip(entity_ids, embeddings):
                    stmt = (
                        update(CarbonEntity)
                        .where(CarbonEntity.id == entity_id)
                        .values(embedding=embedding)
                    )
                    await db.execute(stmt)

                await db.commit()

                processed += len(entities)

                logger.info(
                    "batch_embedded",
                    batch_size=len(entities),
                    total_processed=processed,
                    progress_pct=round(100 * processed / total_count, 1),
                )

                print(f"Processed: {processed:,} / {total_count:,} ({100*processed/total_count:.1f}%)")

            except Exception as e:
                failed += len(entities)
                logger.error(
                    "batch_embedding_failed",
                    error=str(e),
                    batch_start=processed,
                    batch_size=len(entities),
                )
                print(f"Error processing batch: {e}")
                continue

    print()
    print(f"{'='*60}")
    print("Embedding Complete!")
    print(f"{'='*60}")
    print(f"Total processed: {processed:,}")
    print(f"Total failed: {failed:,}")
    print(f"Success rate: {100*(processed-failed)/max(processed,1):.1f}%")
    print()

    logger.info(
        "embedding_complete",
        total_processed=processed,
        total_failed=failed,
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate embeddings for entities in database"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for processing (default: 100)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of entities to process (default: all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Regenerate embeddings for all entities (not just missing)",
    )

    args = parser.parse_args()

    asyncio.run(
        embed_entities(
            batch_size=args.batch_size,
            limit=args.limit,
            only_missing=not args.all,
        )
    )


if __name__ == "__main__":
    main()
