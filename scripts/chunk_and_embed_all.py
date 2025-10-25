"""
Chunk and Embed All Entities.

Processes all carbon entities:
1. Detects entities without embeddings
2. For large entities (>1500 chars), creates document chunks
3. Generates embeddings for all entities and chunks
4. Stores embeddings in PostgreSQL with pgvector

This script is designed to handle large-scale datasets (10,000+ entities)
with efficient batch processing and progress reporting.
"""

import asyncio
from datetime import UTC, datetime

from sqlalchemy import func, select

from mothra.agents.embedding.vector_manager import VectorManager
from mothra.db.models import CarbonEntity
from mothra.db.models_chunks import DocumentChunk
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


async def get_statistics() -> dict:
    """Get current database statistics."""
    async with get_db_context() as db:
        # Total entities
        total_entities_stmt = select(func.count()).select_from(CarbonEntity)
        total_entities = await db.scalar(total_entities_stmt) or 0

        # Entities with embeddings
        embedded_stmt = select(func.count()).select_from(CarbonEntity).where(
            CarbonEntity.embedding.is_not(None)
        )
        embedded_entities = await db.scalar(embedded_stmt) or 0

        # Entities without embeddings
        unembedded_entities = total_entities - embedded_entities

        # Total chunks
        total_chunks_stmt = select(func.count()).select_from(DocumentChunk)
        total_chunks = await db.scalar(total_chunks_stmt) or 0

        # Chunks with embeddings
        embedded_chunks_stmt = select(func.count()).select_from(DocumentChunk).where(
            DocumentChunk.embedding.is_not(None)
        )
        embedded_chunks = await db.scalar(embedded_chunks_stmt) or 0

        return {
            "total_entities": total_entities,
            "embedded_entities": embedded_entities,
            "unembedded_entities": unembedded_entities,
            "total_chunks": total_chunks,
            "embedded_chunks": embedded_chunks,
        }


async def chunk_and_embed_all(batch_size: int = 100) -> dict:
    """
    Process all entities without embeddings.

    Args:
        batch_size: Number of entities to process per batch

    Returns:
        Processing statistics
    """
    start_time = datetime.now(UTC)

    # Initialize vector manager
    vector_manager = VectorManager()

    # Get entities without embeddings
    async with get_db_context() as db:
        stmt = select(CarbonEntity).where(CarbonEntity.embedding.is_(None))
        result = await db.execute(stmt)
        entities = result.scalars().all()

    total_entities = len(entities)
    logger.info("processing_started", total_entities=total_entities)

    print(f"\nProcessing {total_entities:,} entities...")

    # Track statistics
    processed = 0
    chunked_count = 0
    total_chunks_created = 0
    errors = 0

    # Process in batches
    for i in range(0, total_entities, batch_size):
        batch = entities[i : i + batch_size]

        for entity in batch:
            try:
                # Prepare entity data for embedding
                entity_data = {
                    "name": entity.name,
                    "description": entity.description,
                    "entity_type": entity.entity_type,
                    "category_hierarchy": entity.category_hierarchy,
                    "geographic_scope": entity.geographic_scope,
                    "custom_tags": entity.custom_tags,
                }

                # Create searchable text to check size
                text_repr = vector_manager.create_searchable_text(entity_data)

                # Track if this entity needs chunking
                needs_chunking = len(text_repr) > 1500

                # Embed and store (handles chunking internally)
                await vector_manager.embed_and_store_entity(entity.id, entity_data)

                processed += 1

                if needs_chunking:
                    chunked_count += 1
                    # Count chunks created for this entity
                    async with get_db_context() as db:
                        chunk_count_stmt = (
                            select(func.count())
                            .select_from(DocumentChunk)
                            .where(DocumentChunk.entity_id == entity.id)
                        )
                        chunks = await db.scalar(chunk_count_stmt) or 0
                        total_chunks_created += chunks

            except Exception as e:
                errors += 1
                logger.error(
                    "entity_processing_failed",
                    entity_id=str(entity.id),
                    error=str(e),
                )

        # Progress update
        progress_pct = (i + len(batch)) / total_entities * 100
        print(
            f"Progress: {i + len(batch):,}/{total_entities:,} ({progress_pct:.1f}%) - "
            f"Chunked: {chunked_count:,} - Chunks created: {total_chunks_created:,}"
        )

        # Small delay between batches
        await asyncio.sleep(0.1)

    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    stats = {
        "total_entities": total_entities,
        "processed": processed,
        "chunked_entities": chunked_count,
        "total_chunks_created": total_chunks_created,
        "errors": errors,
        "duration_seconds": duration,
        "entities_per_second": processed / duration if duration > 0 else 0,
    }

    logger.info("processing_complete", **stats)

    return stats


async def main():
    """Main execution function."""
    print("=" * 80)
    print("Chunk and Embed All Carbon Entities")
    print("=" * 80)

    # Get initial statistics
    print("\nInitial Database State:")
    print("-" * 80)
    initial_stats = await get_statistics()
    print(f"Total Entities: {initial_stats['total_entities']:,}")
    print(f"Embedded Entities: {initial_stats['embedded_entities']:,}")
    print(f"Unembedded Entities: {initial_stats['unembedded_entities']:,}")
    print(f"Total Chunks: {initial_stats['total_chunks']:,}")
    print(f"Embedded Chunks: {initial_stats['embedded_chunks']:,}")

    if initial_stats['unembedded_entities'] == 0:
        print("\n✅ All entities already have embeddings!")
        return

    # Process entities
    print("\n" + "=" * 80)
    print("Starting Processing...")
    print("=" * 80)

    start_time = datetime.now(UTC)
    processing_stats = await chunk_and_embed_all(batch_size=100)
    end_time = datetime.now(UTC)

    # Get final statistics
    print("\n" + "=" * 80)
    print("Final Database State:")
    print("-" * 80)
    final_stats = await get_statistics()
    print(f"Total Entities: {final_stats['total_entities']:,}")
    print(f"Embedded Entities: {final_stats['embedded_entities']:,}")
    print(f"Unembedded Entities: {final_stats['unembedded_entities']:,}")
    print(f"Total Chunks: {final_stats['total_chunks']:,}")
    print(f"Embedded Chunks: {final_stats['embedded_chunks']:,}")

    # Summary
    print("\n" + "=" * 80)
    print("Processing Summary:")
    print("-" * 80)
    print(f"Entities Processed: {processing_stats['processed']:,}")
    print(f"Large Entities (Chunked): {processing_stats['chunked_entities']:,}")
    print(f"Document Chunks Created: {processing_stats['total_chunks_created']:,}")
    print(f"Errors: {processing_stats['errors']:,}")
    print(f"Duration: {processing_stats['duration_seconds']:.1f} seconds")
    print(
        f"Rate: {processing_stats['entities_per_second']:.1f} entities/second"
    )

    # Calculate chunk statistics
    if processing_stats['chunked_entities'] > 0:
        avg_chunks = (
            processing_stats['total_chunks_created']
            / processing_stats['chunked_entities']
        )
        print(f"Average Chunks per Large Entity: {avg_chunks:.1f}")

    print("\n" + "=" * 80)
    print("✅ Processing Complete!")
    print("=" * 80)

    print("\nNext Steps:")
    print("1. Test semantic search: python scripts/test_search.py")
    print("2. Test chunk-aware search with large documents")
    print("3. Query specific sectors or geographies")


if __name__ == "__main__":
    asyncio.run(main())
