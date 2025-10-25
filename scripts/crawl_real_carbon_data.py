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
        return 0

    print("\nCrawling parseable sources:")
    for source, parser_name in parseable:
        print(f"  - {source.name} → {parser_name}")

    # Crawl with the crawler orchestrator
    async with CrawlerOrchestrator() as crawler:
        entities_before = await get_total_entities()

        print("\n" + "-" * 80)
        print("Crawling in progress...")
        print("-" * 80)

        # Crawl each parseable source
        for source, parser_name in parseable:
            print(f"\n📡 Crawling: {source.name}")
            try:
                await crawler.process_source(source)
                print(f"   ✅ Success")
            except Exception as e:
                print(f"   ❌ Error: {e}")
                logger.error("crawl_failed", source=source.name, error=str(e))

        entities_after = await get_total_entities()
        new_entities = entities_after - entities_before

    print(f"\n✅ Crawling complete! Added {new_entities:,} new entities")
    return new_entities


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
    new_entities = await crawl_with_parsers()

    # Step 3: Analyze taxonomy
    if new_entities > 0 or stats_before['total_entities'] > 0:
        await analyze_taxonomy()

        # Step 4: Show samples
        await show_sample_entities()

    # Final summary
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 80)
    print("🎉 Crawling Complete!")
    print("=" * 80)

    stats_after = await get_database_stats()
    print(f"\nFinal Statistics:")
    print(f"  Total Entities: {stats_after['total_entities']:,}")
    print(f"  New Entities: {stats_after['total_entities'] - stats_before['total_entities']:,}")
    print(f"  Active Sources: {stats_after['active_sources']}")
    print(f"  Duration: {duration:.1f} seconds")

    print("\n📖 Next Steps:")
    print("1. Generate embeddings: python scripts/chunk_and_embed_all.py")
    print("2. Test semantic search: python scripts/test_search.py")
    print("3. Explore taxonomy and categories in database")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
