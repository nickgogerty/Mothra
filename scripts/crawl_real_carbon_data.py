"""
Crawl Real Carbon Emissions Data from Government Sources.

This script activates the parsers and crawlers to fetch REAL carbon data from:
- UK Carbon Intensity API (live grid emissions)
- UK DEFRA Conversion Factors (official emission factors)
- EPA GHGRP (US facility emissions - if available)
- EU ETS (European verified emissions - if available)
- IPCC Emission Factor Database
- EPD Registries (product carbon footprints)

Builds a real taxonomy from government data and populates the database.
"""

import asyncio
from datetime import UTC, datetime

from sqlalchemy import func, select

from mothra.agents.crawler.crawler_agent import CrawlerOrchestrator
from mothra.agents.survey.survey_agent import SurveyAgent
from mothra.db.models import CarbonEntity, DataSource
from mothra.db.session import get_db_context, init_db
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


async def get_database_stats():
    """Get current database statistics."""
    async with get_db_context() as db:
        # Total entities
        total_stmt = select(func.count()).select_from(CarbonEntity)
        total = await db.scalar(total_stmt) or 0

        # Entities with embeddings
        embedded_stmt = select(func.count()).select_from(CarbonEntity).where(
            CarbonEntity.embedding.is_not(None)
        )
        embedded = await db.scalar(embedded_stmt) or 0

        # Entities by type
        type_stmt = select(
            CarbonEntity.entity_type, func.count(CarbonEntity.id)
        ).group_by(CarbonEntity.entity_type)
        result = await db.execute(type_stmt)
        by_type = dict(result.all())

        # Entities by source
        source_stmt = select(
            CarbonEntity.source_id, func.count(CarbonEntity.id)
        ).group_by(CarbonEntity.source_id)
        result = await db.execute(source_stmt)
        by_source = dict(result.all())

        # Total sources
        sources_stmt = select(func.count()).select_from(DataSource)
        total_sources = await db.scalar(sources_stmt) or 0

        # Active sources (with entities)
        active_sources_stmt = (
            select(func.count(func.distinct(CarbonEntity.source_id)))
            .select_from(CarbonEntity)
        )
        active_sources = await db.scalar(active_sources_stmt) or 0

        return {
            "total_entities": total,
            "embedded_entities": embedded,
            "by_type": by_type,
            "by_source": by_source,
            "total_sources": total_sources,
            "active_sources": active_sources,
        }


async def discover_sources():
    """Run survey agent to discover and validate sources."""
    print("\n" + "=" * 80)
    print("Step 1: Discovering Carbon Data Sources")
    print("=" * 80)

    async with SurveyAgent() as agent:
        sources_count = await agent.discover_sources()

    print(f"\n✅ Discovered {sources_count} carbon data sources")

    # Show sources by type
    async with get_db_context() as db:
        stmt = select(
            DataSource.source_type, func.count(DataSource.id)
        ).group_by(DataSource.source_type)
        result = await db.execute(stmt)
        by_type = dict(result.all())

        print("\nSources by Type:")
        for source_type, count in by_type.items():
            print(f"  {source_type}: {count}")

    return sources_count


async def get_parseable_sources():
    """Get sources that have parsers available."""
    from mothra.agents.parser.parser_registry import ParserRegistry

    async with get_db_context() as db:
        # Get all sources
        stmt = select(DataSource)
        result = await db.execute(stmt)
        sources = result.scalars().all()

        parseable = []
        unparseable = []

        for source in sources:
            parser = ParserRegistry.get_parser(source)
            if parser:
                parseable.append((source, parser.__class__.__name__))
            else:
                unparseable.append(source)

        return parseable, unparseable


async def crawl_with_parsers():
    """Crawl sources that have parsers and collect entities."""
    print("\n" + "=" * 80)
    print("Step 2: Crawling Sources with Parsers")
    print("=" * 80)

    parseable, unparseable = await get_parseable_sources()

    print(f"\nSources with Parsers: {len(parseable)}")
    print(f"Sources without Parsers: {len(unparseable)}")

    if not parseable:
        print("\n⚠️  No parseable sources found!")
        print("Run the survey agent first to discover sources.")
        return {
            "total_new_entities": 0,
            "sources_attempted": 0,
            "sources_succeeded": 0,
            "sources_failed": 0,
            "per_source": {},
        }

    print("\nCrawling parseable sources:")
    for source, parser_name in parseable:
        print(f"  - {source.name} → {parser_name}")

    # Track statistics per source
    source_stats = {}
    sources_succeeded = 0
    sources_failed = 0

    # Crawl with the crawler orchestrator
    async with CrawlerOrchestrator() as crawler:
        total_before = await get_total_entities()

        print("\n" + "-" * 80)
        print("Crawling in progress...")
        print("-" * 80)

        # Crawl each parseable source
        for source, parser_name in parseable:
            print(f"\n📡 Crawling: {source.name}")

            # Get entity count before this source
            entities_before = await get_total_entities()

            try:
                await crawler.process_source(source)

                # Get entity count after this source
                entities_after = await get_total_entities()
                entities_added = entities_after - entities_before

                source_stats[source.name] = {
                    "status": "success",
                    "entities_added": entities_added,
                    "parser": parser_name,
                    "error": None,
                }

                sources_succeeded += 1
                print(f"   ✅ Success - Added {entities_added} entities")

            except Exception as e:
                source_stats[source.name] = {
                    "status": "failed",
                    "entities_added": 0,
                    "parser": parser_name,
                    "error": str(e),
                }

                sources_failed += 1
                print(f"   ❌ Error: {e}")
                logger.error("crawl_failed", source=source.name, error=str(e))

        total_after = await get_total_entities()
        total_new = total_after - total_before

    return {
        "total_new_entities": total_new,
        "sources_attempted": len(parseable),
        "sources_succeeded": sources_succeeded,
        "sources_failed": sources_failed,
        "per_source": source_stats,
    }


async def get_total_entities():
    """Get total entity count."""
    async with get_db_context() as db:
        stmt = select(func.count()).select_from(CarbonEntity)
        return await db.scalar(stmt) or 0


async def analyze_taxonomy():
    """Analyze the taxonomy from collected entities."""
    print("\n" + "=" * 80)
    print("Step 3: Analyzing Carbon Taxonomy")
    print("=" * 80)

    stats = await get_database_stats()

    print("\n📊 Database Statistics:")
    print(f"  Total Entities: {stats['total_entities']:,}")
    print(f"  Total Sources: {stats['total_sources']}")
    print(f"  Active Sources (with data): {stats['active_sources']}")

    print("\n📁 Entities by Type:")
    for entity_type, count in sorted(
        stats['by_type'].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {entity_type}: {count:,}")

    print("\n📚 Entities by Source:")
    for source_id, count in sorted(
        stats['by_source'].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"  {source_id}: {count:,}")

    # Analyze category hierarchies
    await analyze_categories()

    # Analyze geographic coverage
    await analyze_geography()


async def analyze_categories():
    """Analyze category hierarchies to build taxonomy."""
    print("\n🏷️  Category Taxonomy:")

    async with get_db_context() as db:
        # Get all unique category hierarchies
        stmt = select(CarbonEntity.category_hierarchy).distinct()
        result = await db.execute(stmt)
        hierarchies = [row[0] for row in result.all() if row[0]]

        # Build a tree structure
        category_tree = {}
        for hierarchy in hierarchies:
            if not hierarchy:
                continue

            current = category_tree
            for level, category in enumerate(hierarchy):
                if category not in current:
                    current[category] = {}
                current = current[category]

        # Print tree
        def print_tree(tree, indent=0):
            for key in sorted(tree.keys()):
                print("  " * indent + f"├─ {key}")
                if tree[key]:
                    print_tree(tree[key], indent + 1)

        print_tree(category_tree)


async def analyze_geography():
    """Analyze geographic coverage."""
    print("\n🌍 Geographic Coverage:")

    async with get_db_context() as db:
        # Get all unique geographic scopes
        stmt = select(CarbonEntity.geographic_scope).distinct()
        result = await db.execute(stmt)

        all_regions = set()
        for row in result.all():
            if row[0]:
                all_regions.update(row[0])

        # Count entities per region
        region_counts = {}
        for region in all_regions:
            count_stmt = select(func.count()).select_from(CarbonEntity).where(
                CarbonEntity.geographic_scope.contains([region])
            )
            count = await db.scalar(count_stmt) or 0
            region_counts[region] = count

        # Print sorted by count
        for region, count in sorted(
            region_counts.items(), key=lambda x: x[1], reverse=True
        )[:20]:  # Top 20
            print(f"  {region}: {count:,} entities")


async def show_sample_entities():
    """Show sample entities from each type."""
    print("\n" + "=" * 80)
    print("Step 4: Sample Entities")
    print("=" * 80)

    async with get_db_context() as db:
        # Get entity types
        type_stmt = select(CarbonEntity.entity_type).distinct()
        result = await db.execute(type_stmt)
        types = [row[0] for row in result.all() if row[0]]

        for entity_type in types[:5]:  # Show first 5 types
            print(f"\n📄 Sample {entity_type.upper()} entities:")

            stmt = (
                select(CarbonEntity)
                .where(CarbonEntity.entity_type == entity_type)
                .limit(3)
            )
            result = await db.execute(stmt)
            entities = result.scalars().all()

            for i, entity in enumerate(entities, 1):
                print(f"\n  {i}. {entity.name}")
                print(f"     Source: {entity.source_id}")
                if entity.category_hierarchy:
                    categories = " > ".join(entity.category_hierarchy[:3])
                    print(f"     Categories: {categories}")
                if entity.geographic_scope:
                    regions = ", ".join(entity.geographic_scope[:3])
                    print(f"     Regions: {regions}")
                desc_preview = entity.description[:150] if entity.description else "N/A"
                print(f"     Description: {desc_preview}...")


async def print_crawl_summary(crawl_results, stats_before, stats_after, duration):
    """Print comprehensive crawl summary report."""
    print("\n" + "=" * 80)
    print("📊 CRAWL SUMMARY REPORT")
    print("=" * 80)

    # Overall Statistics
    print("\n┌─ Overall Statistics ─────────────────────────────────────────────┐")
    print(f"│ Total Entities Before:        {stats_before['total_entities']:>6,}                           │")
    print(f"│ Total Entities After:         {stats_after['total_entities']:>6,}                           │")
    print(f"│ New Entities Added:           {crawl_results['total_new_entities']:>6,}                           │")
    print(f"│ Duration:                     {duration:>6.1f}s                          │")
    print(f"│ Rate:                         {crawl_results['total_new_entities']/duration if duration > 0 else 0:>6.1f} entities/sec              │")
    print("└──────────────────────────────────────────────────────────────────┘")

    # Source Success Rate
    print("\n┌─ Source Crawl Results ───────────────────────────────────────────┐")
    print(f"│ Sources Attempted:            {crawl_results['sources_attempted']:>6}                            │")
    print(f"│ Sources Succeeded:            {crawl_results['sources_succeeded']:>6} ✅                         │")
    print(f"│ Sources Failed:               {crawl_results['sources_failed']:>6} ❌                         │")
    success_rate = (
        crawl_results['sources_succeeded'] / crawl_results['sources_attempted'] * 100
        if crawl_results['sources_attempted'] > 0 else 0
    )
    print(f"│ Success Rate:                 {success_rate:>6.1f}%                          │")
    print("└──────────────────────────────────────────────────────────────────┘")

    # Per-Source Breakdown
    if crawl_results['per_source']:
        print("\n┌─ Detailed Source Breakdown ──────────────────────────────────────┐")
        print("│                                                                  │")

        for source_name, stats in sorted(
            crawl_results['per_source'].items(),
            key=lambda x: x[1]['entities_added'],
            reverse=True
        ):
            status_icon = "✅" if stats['status'] == 'success' else "❌"
            print(f"│ {status_icon} {source_name[:45]:<45} │")
            print(f"│   Parser: {stats['parser'][:50]:<50}   │")
            print(f"│   Entities Added: {stats['entities_added']:>6,}                                   │")

            if stats['error']:
                error_preview = stats['error'][:48]
                print(f"│   Error: {error_preview:<51}│")

            print("│                                                                  │")

        print("└──────────────────────────────────────────────────────────────────┘")

    # Data Distribution
    print("\n┌─ Data Distribution ──────────────────────────────────────────────┐")
    print("│                                                                  │")
    print("│ By Entity Type:                                                  │")
    for entity_type, count in sorted(
        stats_after['by_type'].items(), key=lambda x: x[1], reverse=True
    )[:5]:
        print(f"│   {entity_type[:20]:<20}: {count:>6,}                                │")

    print("│                                                                  │")
    print("│ By Source:                                                       │")
    for source_id, count in sorted(
        stats_after['by_source'].items(), key=lambda x: x[1], reverse=True
    )[:5]:
        print(f"│   {source_id[:20]:<20}: {count:>6,}                                │")

    print("└──────────────────────────────────────────────────────────────────┘")

    # Data Quality Indicators
    print("\n┌─ Data Quality Indicators ────────────────────────────────────────┐")
    entities_with_embeddings = stats_after.get('embedded_entities', 0)
    embedding_coverage = (
        entities_with_embeddings / stats_after['total_entities'] * 100
        if stats_after['total_entities'] > 0 else 0
    )
    print(f"│ Entities with Embeddings:     {entities_with_embeddings:>6,} ({embedding_coverage:>5.1f}%)                │")
    print(f"│ Active Data Sources:          {stats_after['active_sources']:>6}                            │")
    print(f"│ Total Data Sources:           {stats_after['total_sources']:>6}                            │")
    source_coverage = (
        stats_after['active_sources'] / stats_after['total_sources'] * 100
        if stats_after['total_sources'] > 0 else 0
    )
    print(f"│ Source Coverage:              {source_coverage:>6.1f}%                          │")
    print("└──────────────────────────────────────────────────────────────────┘")


async def main():
    """Main execution."""
    print("=" * 80)
    print("MOTHRA - Real Carbon Data Crawler")
    print("=" * 80)
    print("\nThis script will crawl REAL government carbon emissions data")
    print("and build an actual taxonomy from authoritative sources.")

    start_time = datetime.now(UTC)

    # Initialize database
    print("\n🔧 Initializing database...")
    await init_db()
    print("✅ Database ready")

    # Show initial stats
    stats_before = await get_database_stats()
    print(f"\nInitial state: {stats_before['total_entities']:,} entities")

    # Step 1: Discover sources
    await discover_sources()

    # Step 2: Crawl with parsers
    crawl_results = await crawl_with_parsers()

    # Step 3: Analyze taxonomy
    if crawl_results['total_new_entities'] > 0 or stats_before['total_entities'] > 0:
        await analyze_taxonomy()

        # Step 4: Show samples
        await show_sample_entities()

    # Final summary with detailed report
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    stats_after = await get_database_stats()

    # Print comprehensive summary report
    await print_crawl_summary(crawl_results, stats_before, stats_after, duration)

    print("\n" + "=" * 80)
    print("🎉 Crawling Complete!")
    print("=" * 80)

    print("\n📖 Next Steps:")
    print("1. Generate embeddings: python scripts/chunk_and_embed_all.py")
    print("2. Test semantic search: python scripts/test_search.py")
    print("3. Explore taxonomy and categories in database")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
