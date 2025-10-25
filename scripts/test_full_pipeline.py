"""
Test Full MOTHRA Pipeline End-to-End.

This script demonstrates the complete MOTHRA architecture:
1. Survey Agent - Discovers data sources
2. Crawler - Fetches data from sources
3. Parser Registry - Automatically selects parsers
4. Parsers - Extract carbon entities
5. Database - Stores entities
6. Embedding Agent - Generates vectors
7. Semantic Search - Natural language queries

This is the ultimate test of the MOTHRA system!
"""

import asyncio
from datetime import datetime

from sqlalchemy import select, func

from mothra.agents.survey.survey_agent import SurveyAgent
from mothra.agents.crawler.crawler_agent import CrawlerOrchestrator
from mothra.agents.parser.parser_registry import ParserRegistry
from mothra.agents.embedding.vector_manager import VectorManager
from mothra.db.models import CarbonEntity, CrawlLog, DataSource
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


async def get_database_stats() -> dict:
    """Get current database statistics."""
    async with get_db_context() as db:
        # Count sources by status
        stmt = select(DataSource.status, func.count(DataSource.id)).group_by(DataSource.status)
        result = await db.execute(stmt)
        sources_by_status = dict(result.fetchall())

        # Count total entities
        stmt = select(func.count(CarbonEntity.id))
        result = await db.execute(stmt)
        total_entities = result.scalar_one()

        # Count entities with embeddings
        stmt = select(func.count(CarbonEntity.id)).where(CarbonEntity.embedding.isnot(None))
        result = await db.execute(stmt)
        entities_with_embeddings = result.scalar_one()

        # Count entities by type
        stmt = select(CarbonEntity.entity_type, func.count(CarbonEntity.id)).group_by(CarbonEntity.entity_type)
        result = await db.execute(stmt)
        entities_by_type = dict(result.fetchall())

        # Recent crawl logs
        stmt = select(func.count(CrawlLog.id))
        result = await db.execute(stmt)
        total_crawls = result.scalar_one()

        return {
            "sources_by_status": sources_by_status,
            "total_entities": total_entities,
            "entities_with_embeddings": entities_with_embeddings,
            "entities_by_type": entities_by_type,
            "total_crawls": total_crawls,
        }


async def show_stats(title: str, stats: dict):
    """Display database statistics."""
    print(f"\n{'=' * 80}")
    print(f"{title}")
    print('=' * 80)

    print(f"\n📊 Data Sources:")
    for status, count in stats["sources_by_status"].items():
        print(f"   {status}: {count}")

    print(f"\n📦 Carbon Entities:")
    print(f"   Total: {stats['total_entities']}")
    print(f"   With embeddings: {stats['entities_with_embeddings']}")
    print(f"   Without embeddings: {stats['total_entities'] - stats['entities_with_embeddings']}")

    if stats["entities_by_type"]:
        print(f"\n🏷️  By Type:")
        for entity_type, count in stats["entities_by_type"].items():
            print(f"   {entity_type}: {count}")

    print(f"\n📝 Crawl Logs: {stats['total_crawls']}")


async def show_parser_coverage():
    """Show which sources have parsers available."""
    print(f"\n{'=' * 80}")
    print("Parser Coverage Analysis")
    print('=' * 80)

    async with get_db_context() as db:
        stmt = select(DataSource).where(DataSource.status.in_(["validated", "active"]))
        result = await db.execute(stmt)
        sources = result.scalars().all()

        sources_with_parsers = []
        sources_without_parsers = []

        for source in sources:
            if ParserRegistry.has_parser(source):
                parser = ParserRegistry.get_parser(source)
                sources_with_parsers.append((source, parser.__class__.__name__))
            else:
                sources_without_parsers.append(source)

        print(f"\n✅ Sources with Parsers: {len(sources_with_parsers)}")
        for source, parser_name in sources_with_parsers:
            print(f"   • {source.name}")
            print(f"     → {parser_name}")
            print(f"     Priority: {source.priority}, Format: {source.data_format}")

        print(f"\n⚠️  Sources without Parsers: {len(sources_without_parsers)}")
        for source in sources_without_parsers[:10]:  # Show first 10
            print(f"   • {source.name}")
            print(f"     Format: {source.data_format}, Priority: {source.priority}")

        if len(sources_without_parsers) > 10:
            print(f"   ... and {len(sources_without_parsers) - 10} more")

        return sources_with_parsers, sources_without_parsers


async def run_crawler_on_parser_sources(sources_with_parsers: list):
    """Run crawler only on sources that have parsers."""
    print(f"\n{'=' * 80}")
    print(f"Running Crawler on {len(sources_with_parsers)} Parser-Enabled Sources")
    print('=' * 80)

    if not sources_with_parsers:
        print("\n⚠️  No sources with parsers available")
        return

    print("\nThis may take a few minutes depending on API response times...")
    print("Processing sources:")
    for source, parser_name in sources_with_parsers:
        print(f"  • {source.name} ({parser_name})")

    async with CrawlerOrchestrator() as crawler:
        # Add sources to queue
        for source, _ in sources_with_parsers:
            await crawler.crawl_queue.put(source)

        # Process all sources
        workers = [
            asyncio.create_task(crawler.worker(f"worker-{i}"))
            for i in range(min(3, len(sources_with_parsers)))  # Use 3 workers max
        ]

        # Wait for completion
        await crawler.crawl_queue.join()

        # Cancel workers
        for worker in workers:
            worker.cancel()

        await asyncio.gather(*workers, return_exceptions=True)

    print("\n✅ Crawler complete!")


async def show_recent_crawl_logs():
    """Display recent crawl results."""
    print(f"\n{'=' * 80}")
    print("Recent Crawl Results")
    print('=' * 80)

    async with get_db_context() as db:
        stmt = (
            select(CrawlLog, DataSource)
            .join(DataSource, CrawlLog.source_id == DataSource.id)
            .order_by(CrawlLog.started_at.desc())
            .limit(10)
        )
        result = await db.execute(stmt)
        logs = result.fetchall()

        if not logs:
            print("\nNo crawl logs found.")
            return

        total_found = 0
        total_processed = 0

        for i, (log, source) in enumerate(logs, 1):
            status_icon = "✅" if log.status == "success" else "❌"
            print(f"\n{i}. {status_icon} {source.name}")
            print(f"   Status: {log.status}")
            print(f"   Duration: {log.duration_seconds:.2f}s")
            print(f"   Records Found: {log.records_found}")
            print(f"   Records Processed: {log.records_processed}")
            if log.error_message:
                print(f"   Error: {log.error_message[:100]}")

            total_found += log.records_found
            total_processed += log.records_processed

        print(f"\n📊 Summary:")
        print(f"   Total Records Found: {total_found}")
        print(f"   Total Records Processed: {total_processed}")


async def generate_embeddings():
    """Generate embeddings for all entities without them."""
    print(f"\n{'=' * 80}")
    print("Generating Embeddings")
    print('=' * 80)

    manager = VectorManager()
    print(f"\nUsing model: {manager.model_name}")
    print(f"Embedding dimension: {manager.dimension}")

    # Check how many need embeddings
    async with get_db_context() as db:
        stmt = select(func.count(CarbonEntity.id)).where(CarbonEntity.embedding.is_(None))
        result = await db.execute(stmt)
        count_without = result.scalar_one()

    if count_without == 0:
        print("\n✅ All entities already have embeddings!")
        return

    print(f"\nGenerating embeddings for {count_without} entities...")
    reindexed = await manager.reindex_all()

    print(f"\n✅ Generated {reindexed} embeddings!")


async def test_semantic_search():
    """Test semantic search with various queries."""
    print(f"\n{'=' * 80}")
    print("Testing Semantic Search")
    print('=' * 80)

    manager = VectorManager()

    test_queries = [
        "electricity grid carbon intensity",
        "steel production emissions",
        "concrete carbon footprint",
        "natural gas emission factor",
        "facility greenhouse gas emissions",
        "renewable energy sources",
    ]

    print("\nRunning test queries...\n")

    all_results = []
    for query in test_queries:
        print(f"🔍 Query: '{query}'")

        results = await manager.semantic_search(
            query=query,
            limit=3,
            similarity_threshold=0.3,
        )

        if results:
            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results[:3], 1):
                print(f"   {i}. {result['name'][:60]}")
                print(f"      Similarity: {result['similarity']:.3f} ({result['similarity']*100:.1f}%)")
            all_results.extend(results)
        else:
            print(f"   No results found")

        print()

    return all_results


async def show_sample_entities():
    """Show sample entities from database."""
    print(f"\n{'=' * 80}")
    print("Sample Entities")
    print('=' * 80)

    async with get_db_context() as db:
        stmt = select(CarbonEntity).order_by(CarbonEntity.created_at.desc()).limit(10)
        result = await db.execute(stmt)
        entities = result.scalars().all()

        for i, entity in enumerate(entities, 1):
            print(f"\n{i}. {entity.name[:70]}")
            print(f"   Type: {entity.entity_type}")
            print(f"   Source: {entity.source_id}")
            if entity.category_hierarchy:
                print(f"   Category: {' > '.join(entity.category_hierarchy[:3])}")
            if entity.geographic_scope:
                print(f"   Geographic: {', '.join(entity.geographic_scope[:3])}")
            print(f"   Quality: {entity.quality_score}")
            print(f"   Has Embedding: {'✅' if entity.embedding is not None else '❌'}")


async def main():
    """Run full pipeline test."""
    start_time = datetime.now()

    print("=" * 80)
    print("🚀 MOTHRA FULL PIPELINE TEST")
    print("=" * 80)
    print("\nTesting complete end-to-end pipeline:")
    print("Survey → Crawl → Parse → Store → Embed → Search")
    print(f"\nStarted at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Initial stats
    print(f"\n{'=' * 80}")
    print("STEP 1: Initial Database State")
    print('=' * 80)
    stats_before = await get_database_stats()
    await show_stats("Before Pipeline Run", stats_before)

    # Step 2: Survey sources
    print(f"\n{'=' * 80}")
    print("STEP 2: Survey Data Sources")
    print('=' * 80)
    print("\nDiscovering and validating sources from catalog...")
    async with SurveyAgent() as agent:
        sources_count = await agent.discover_sources()
    print(f"\n✅ Survey complete!")
    print(f"   Sources discovered: {sources_count}")

    # Step 3: Check parser coverage
    print(f"\n{'=' * 80}")
    print("STEP 3: Analyze Parser Coverage")
    print('=' * 80)
    sources_with_parsers, sources_without = await show_parser_coverage()

    # Step 4: Run crawler
    print(f"\n{'=' * 80}")
    print("STEP 4: Crawl Parser-Enabled Sources")
    print('=' * 80)
    await run_crawler_on_parser_sources(sources_with_parsers)

    # Step 5: Show crawl results
    await show_recent_crawl_logs()

    # Step 6: Check new stats
    print(f"\n{'=' * 80}")
    print("STEP 5: Database State After Crawling")
    print('=' * 80)
    stats_after_crawl = await get_database_stats()
    await show_stats("After Crawling", stats_after_crawl)

    # Step 7: Generate embeddings
    print(f"\n{'=' * 80}")
    print("STEP 6: Generate Embeddings")
    print('=' * 80)
    await generate_embeddings()

    # Step 8: Final stats
    print(f"\n{'=' * 80}")
    print("STEP 7: Final Database State")
    print('=' * 80)
    stats_final = await get_database_stats()
    await show_stats("After Embeddings", stats_final)

    # Step 9: Test search
    print(f"\n{'=' * 80}")
    print("STEP 8: Test Semantic Search")
    print('=' * 80)
    search_results = await test_semantic_search()

    # Step 10: Show sample entities
    await show_sample_entities()

    # Final summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n{'=' * 80}")
    print("🎉 PIPELINE TEST COMPLETE!")
    print('=' * 80)

    print(f"\n📊 Summary:")
    print(f"   Duration: {duration:.1f} seconds")
    print(f"   Sources discovered: {sources_count}")
    print(f"   Sources with parsers: {len(sources_with_parsers)}")
    print(f"   Entities before: {stats_before['total_entities']}")
    print(f"   Entities after: {stats_final['total_entities']}")
    print(f"   New entities: {stats_final['total_entities'] - stats_before['total_entities']}")
    print(f"   Entities with embeddings: {stats_final['entities_with_embeddings']}")
    print(f"   Search results tested: {len(search_results) if search_results else 0}")

    print(f"\n✅ MOTHRA is fully operational!")
    print(f"\nYou can now:")
    print(f"   • Query carbon data with natural language")
    print(f"   • Add more parsers for additional sources")
    print(f"   • Schedule periodic crawling")
    print(f"   • Build applications on top of the API")


if __name__ == "__main__":
    asyncio.run(main())
