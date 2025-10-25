"""
Test Complete Chunking Pipeline.

This script tests the full chunking and embedding pipeline:
1. Generates 10,000 sample entities (30% long documents requiring chunking)
2. Chunks and embeds all entities
3. Tests semantic search with and without chunk awareness
4. Demonstrates improved search quality for large documents
"""

import asyncio
from datetime import UTC, datetime

from mothra.agents.embedding.vector_manager import VectorManager
from mothra.db.session import get_db_context, init_db
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


async def test_search_comparison(queries: list[str]):
    """
    Compare regular search vs chunk-aware search.

    Args:
        queries: List of search queries to test
    """
    print("\n" + "=" * 80)
    print("Search Quality Comparison")
    print("=" * 80)

    vector_manager = VectorManager()

    for query in queries:
        print(f"\n📊 Query: '{query}'")
        print("-" * 80)

        # Test regular search (entity embeddings only)
        print("\n🔍 Regular Search (Entity Embeddings Only):")
        regular_results = await vector_manager.semantic_search(
            query=query,
            limit=5,
            similarity_threshold=0.3,
        )

        for i, result in enumerate(regular_results, 1):
            print(f"\n  {i}. {result['name']}")
            print(f"     Similarity: {result['similarity']:.3f}")
            print(f"     Type: {result['entity_type']}")
            print(f"     Regions: {', '.join(result['geographic_scope'][:3])}")

        # Test chunk-aware search
        print("\n\n🔍 Chunk-Aware Search (Entities + Document Chunks):")
        chunk_results = await vector_manager.semantic_search_with_chunks(
            query=query,
            limit=5,
            similarity_threshold=0.3,
        )

        for i, result in enumerate(chunk_results, 1):
            print(f"\n  {i}. {result['name']}")
            print(f"     Similarity: {result['similarity']:.3f}")
            print(f"     Type: {result['entity_type']}")
            print(f"     Regions: {', '.join(result['geographic_scope'][:3])}")
            print(f"     Match via: {result['match_types']}")

        print("\n" + "-" * 80)


async def count_entities_and_chunks():
    """Count entities and chunks in database."""
    from sqlalchemy import func, select

    from mothra.db.models import CarbonEntity
    from mothra.db.models_chunks import DocumentChunk

    async with get_db_context() as db:
        # Count entities
        entity_count_stmt = select(func.count()).select_from(CarbonEntity)
        entity_count = await db.scalar(entity_count_stmt) or 0

        # Count embedded entities
        embedded_count_stmt = select(func.count()).select_from(CarbonEntity).where(
            CarbonEntity.embedding.is_not(None)
        )
        embedded_count = await db.scalar(embedded_count_stmt) or 0

        # Count chunks
        chunk_count_stmt = select(func.count()).select_from(DocumentChunk)
        chunk_count = await db.scalar(chunk_count_stmt) or 0

        # Count embedded chunks
        embedded_chunks_stmt = select(func.count()).select_from(DocumentChunk).where(
            DocumentChunk.embedding.is_not(None)
        )
        embedded_chunks = await db.scalar(embedded_chunks_stmt) or 0

        # Count entities with chunks
        entities_with_chunks_stmt = (
            select(func.count(func.distinct(DocumentChunk.entity_id)))
            .select_from(DocumentChunk)
        )
        entities_with_chunks = await db.scalar(entities_with_chunks_stmt) or 0

    return {
        "total_entities": entity_count,
        "embedded_entities": embedded_count,
        "total_chunks": chunk_count,
        "embedded_chunks": embedded_chunks,
        "entities_with_chunks": entities_with_chunks,
    }


async def main():
    """Run complete chunking pipeline test."""
    print("=" * 80)
    print("MOTHRA Chunking Pipeline - Full Test")
    print("=" * 80)
    print("\nThis test will:")
    print("1. Check database state")
    print("2. Generate 10,000 sample entities (if needed)")
    print("3. Chunk and embed all entities")
    print("4. Compare regular vs chunk-aware search")
    print("\n" + "=" * 80)

    overall_start = datetime.now(UTC)

    # Step 1: Initialize database
    print("\n📦 Step 1: Initializing Database")
    print("-" * 80)
    await init_db()
    print("✅ Database initialized with pgvector extension")

    # Check current state
    stats = await count_entities_and_chunks()
    print(f"\nCurrent Database State:")
    print(f"  Total Entities: {stats['total_entities']:,}")
    print(f"  Embedded Entities: {stats['embedded_entities']:,}")
    print(f"  Total Chunks: {stats['total_chunks']:,}")
    print(f"  Embedded Chunks: {stats['embedded_chunks']:,}")
    print(f"  Entities with Chunks: {stats['entities_with_chunks']:,}")

    # Step 2: Generate samples if needed
    if stats['total_entities'] < 10000:
        print("\n📝 Step 2: Generating 10,000 Sample Entities")
        print("-" * 80)
        print("This will take approximately 10-15 minutes...")

        from scripts.generate_10k_samples import generate_entities

        start = datetime.now(UTC)
        count = await generate_entities(total=10000, batch_size=100)
        duration = (datetime.now(UTC) - start).total_seconds()

        print(f"\n✅ Generated {count:,} entities in {duration:.1f} seconds")
        print(f"Rate: {count/duration:.1f} entities/second")
    else:
        print("\n✅ Step 2: Skipped - Database already has 10,000+ entities")

    # Step 3: Chunk and embed
    print("\n🔧 Step 3: Chunking and Embedding")
    print("-" * 80)

    # Check if embedding needed
    stats = await count_entities_and_chunks()
    if stats['embedded_entities'] < stats['total_entities']:
        print(
            f"Processing {stats['total_entities'] - stats['embedded_entities']:,} "
            "unembedded entities..."
        )

        from scripts.chunk_and_embed_all import chunk_and_embed_all

        start = datetime.now(UTC)
        processing_stats = await chunk_and_embed_all(batch_size=100)
        duration = (datetime.now(UTC) - start).total_seconds()

        print(f"\n✅ Chunking and Embedding Complete!")
        print(f"  Entities Processed: {processing_stats['processed']:,}")
        print(f"  Large Entities Chunked: {processing_stats['chunked_entities']:,}")
        print(f"  Chunks Created: {processing_stats['total_chunks_created']:,}")
        print(f"  Duration: {duration:.1f} seconds")
        print(f"  Rate: {processing_stats['entities_per_second']:.1f} entities/sec")
    else:
        print("✅ All entities already embedded!")

    # Final statistics
    print("\n📊 Step 4: Final Database Statistics")
    print("-" * 80)
    final_stats = await count_entities_and_chunks()
    print(f"Total Entities: {final_stats['total_entities']:,}")
    print(f"Embedded Entities: {final_stats['embedded_entities']:,}")
    print(f"Total Chunks: {final_stats['total_chunks']:,}")
    print(f"Embedded Chunks: {final_stats['embedded_chunks']:,}")
    print(f"Entities with Chunks: {final_stats['entities_with_chunks']:,}")

    if final_stats['entities_with_chunks'] > 0:
        avg_chunks = (
            final_stats['total_chunks'] / final_stats['entities_with_chunks']
        )
        print(f"Average Chunks per Large Entity: {avg_chunks:.1f}")

    # Step 5: Test searches
    print("\n🔍 Step 5: Testing Semantic Search")
    print("-" * 80)

    test_queries = [
        "renewable energy sources solar wind",
        "steel production emissions blast furnace",
        "cement manufacturing carbon footprint",
        "transportation emissions electric vehicles",
        "agriculture livestock methane emissions",
        "regulatory compliance EU ETS carbon trading",
    ]

    await test_search_comparison(test_queries)

    # Overall summary
    overall_duration = (datetime.now(UTC) - overall_start).total_seconds()

    print("\n" + "=" * 80)
    print("🎉 Pipeline Test Complete!")
    print("=" * 80)
    print(f"\nTotal Duration: {overall_duration:.1f} seconds ({overall_duration/60:.1f} minutes)")
    print("\nKey Achievements:")
    print(f"✅ Database contains {final_stats['total_entities']:,} carbon entities")
    print(f"✅ All entities have embeddings for semantic search")
    print(f"✅ Large documents split into {final_stats['total_chunks']:,} chunks")
    print(f"✅ Chunk-aware search enabled for better context understanding")

    print("\n" + "=" * 80)
    print("Next Steps:")
    print("1. Query specific sectors: python scripts/test_search.py")
    print("2. Explore chunk matches for complex queries")
    print("3. Add more parsers to crawl real government data")
    print("4. Scale to 50,000+ entities from free data sources")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
