"""
Test Automated Crawler-Parser Pipeline.

This script tests the full automated pipeline:
Survey → Crawl → Parse → Store → Embed → Search

It demonstrates the crawler automatically:
1. Fetching data from a source
2. Detecting the appropriate parser
3. Parsing the data into CarbonEntity records
4. Storing entities in the database
5. Ready for embedding generation
"""

import asyncio

from sqlalchemy import select

from mothra.agents.crawler.crawler_agent import CrawlerOrchestrator
from mothra.agents.parser.parser_registry import ParserRegistry
from mothra.db.models import CarbonEntity, CrawlLog, DataSource
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


async def setup_test_source() -> DataSource:
    """Set up UK Carbon Intensity API as test source."""
    async with get_db_context() as db:
        # Check if source exists
        stmt = select(DataSource).where(DataSource.name == "UK Carbon Intensity API")
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()

        if not source:
            source = DataSource(
                name="UK Carbon Intensity API",
                url="https://api.carbonintensity.org.uk/intensity",
                source_type="api",
                category="government",
                priority="high",
                access_method="rest",
                auth_required=False,
                rate_limit=3600,
                update_frequency="realtime",
                data_format="json",
                estimated_size_gb=2.0,
                status="active",
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)
            print(f"✅ Created data source: {source.name}")
        else:
            print(f"✅ Using existing data source: {source.name}")

        return source


async def show_parser_registry():
    """Display available parsers."""
    print("\n" + "=" * 80)
    print("Parser Registry")
    print("=" * 80)

    parsers = ParserRegistry.list_parsers()
    print(f"\nRegistered parsers: {len(parsers)}")

    for i, (source_name, parser_name) in enumerate(parsers.items(), 1):
        print(f"  {i}. {source_name}")
        print(f"     → {parser_name}")


async def count_entities_before() -> int:
    """Count existing entities."""
    async with get_db_context() as db:
        stmt = select(CarbonEntity)
        result = await db.execute(stmt)
        entities = result.scalars().all()
        return len(entities)


async def show_new_entities(count_before: int):
    """Display newly created entities."""
    async with get_db_context() as db:
        stmt = select(CarbonEntity).order_by(CarbonEntity.created_at.desc())
        result = await db.execute(stmt)
        all_entities = result.scalars().all()

        new_entities = all_entities[:len(all_entities) - count_before]

        if new_entities:
            print("\n" + "=" * 80)
            print(f"New Entities Created: {len(new_entities)}")
            print("=" * 80)

            for i, entity in enumerate(new_entities[:5], 1):  # Show first 5
                print(f"\n{i}. {entity.name}")
                print(f"   Type: {entity.entity_type}")
                print(f"   Category: {' > '.join(entity.category_hierarchy or [])}")
                print(f"   Geographic Scope: {', '.join(entity.geographic_scope or [])}")
                print(f"   Quality Score: {entity.quality_score}")
                print(f"   Description: {entity.description[:150]}...")

            if len(new_entities) > 5:
                print(f"\n   ... and {len(new_entities) - 5} more entities")
        else:
            print("\n⚠️  No new entities created")


async def show_crawl_log():
    """Display latest crawl log entry."""
    async with get_db_context() as db:
        stmt = select(CrawlLog).order_by(CrawlLog.started_at.desc()).limit(1)
        result = await db.execute(stmt)
        log = result.scalar_one_or_none()

        if log:
            print("\n" + "=" * 80)
            print("Crawl Log")
            print("=" * 80)
            print(f"Status: {log.status}")
            print(f"Duration: {log.duration_seconds:.2f}s")
            print(f"Records Found: {log.records_found}")
            print(f"Records Processed: {log.records_processed}")
            if log.error_message:
                print(f"Error: {log.error_message}")


async def main():
    """Run automated pipeline test."""
    print("=" * 80)
    print("MOTHRA Automated Crawler-Parser Pipeline Test")
    print("=" * 80)

    # Show parser registry
    await show_parser_registry()

    # Set up test source
    print("\n" + "=" * 80)
    print("Step 1: Setup Data Source")
    print("=" * 80)
    source = await setup_test_source()

    # Check if parser exists for source
    has_parser = ParserRegistry.has_parser(source)
    if has_parser:
        parser = ParserRegistry.get_parser(source)
        print(f"✅ Parser available: {parser.__class__.__name__}")
    else:
        print("❌ No parser available for this source")
        return

    # Count entities before
    count_before = await count_entities_before()
    print(f"\nEntities in database before crawl: {count_before}")

    # Run crawler
    print("\n" + "=" * 80)
    print("Step 2: Run Automated Crawler Pipeline")
    print("=" * 80)
    print("Fetching data → Parsing → Storing...\n")

    async with CrawlerOrchestrator() as crawler:
        # Add just our test source to the queue
        await crawler.crawl_queue.put(source)

        # Process it
        await crawler.process_source(source)

    # Show results
    print("\n" + "=" * 80)
    print("Step 3: Results")
    print("=" * 80)

    # Show crawl log
    await show_crawl_log()

    # Show new entities
    await show_new_entities(count_before)

    # Count total entities
    count_after = await count_entities_before()
    new_count = count_after - count_before
    print(f"\n✅ Pipeline Complete!")
    print(f"   Entities before: {count_before}")
    print(f"   Entities after: {count_after}")
    print(f"   New entities: {new_count}")

    # Next steps
    print("\n" + "=" * 80)
    print("Next Steps")
    print("=" * 80)
    print("1. Generate embeddings for new entities:")
    print("   python -m mothra.agents.embedding.vector_manager")
    print("\n2. Search the data:")
    print("   python scripts/test_search.py")
    print("   Try: 'UK electricity grid carbon intensity'")
    print("\n3. Run crawler for all active sources:")
    print("   python -m mothra.agents.crawler.crawler_agent")


if __name__ == "__main__":
    asyncio.run(main())
