"""
Deep Crawl Real Carbon Datasets.

This script goes DEEP to find and ingest real carbon emissions data:
1. Uses WebSearch to discover dataset pages
2. Extracts download links from government pages
3. Downloads Excel/XML/CSV files
4. Automatically maps data to taxonomy
5. Ingests thousands of real entities

Real data sources targeted:
- EPA GHGRP: 16,000+ US facilities with emissions data
- EU ETS: 16,000+ EU installations with verified emissions
- UK DEFRA: 1,000+ emission conversion factors
- National inventories: Various countries
- EPD databases: Product carbon footprints
"""

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import func, select

from mothra.agents.discovery.dataset_discovery import (
    DataFileParser,
    DatasetDiscovery,
    FileDownloader,
    KNOWN_DATASETS,
)
from mothra.db.models import CarbonEntity, DataSource
from mothra.db.session import get_db_context, init_db
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


# Direct download URLs for known high-value datasets
DIRECT_DOWNLOAD_URLS = {
    "UK_DEFRA_2024_CONDENSED": "https://assets.publishing.service.gov.uk/media/667489f1be0a1e0010b84550/2024-ghg-conversion-factors-condensed-set-_v1.1_.xlsx",
    "UK_DEFRA_2024_FULL": "https://assets.publishing.service.gov.uk/media/667489e14db8b100103dd2be/2024-ghg-conversion-factors-full-set.xlsx",
    # Add more as discovered
}


async def register_data_source(name: str, url: str, source_type: str) -> DataSource:
    """Register a data source in the database."""
    async with get_db_context() as db:
        # Check if exists
        stmt = select(DataSource).where(DataSource.name == name)
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()

        if source:
            return source

        # Create new
        source = DataSource(
            name=name,
            source_type=source_type,
            url=url,
            access_method="file_download",
            update_frequency="annual",
            extra_metadata={
                "discovered_by": "deep_crawl",
                "discovery_date": datetime.now(UTC).isoformat(),
            },
        )

        db.add(source)
        await db.commit()
        await db.refresh(source)

        logger.info("data_source_registered", name=name, url=url)

        return source


async def store_entities(entities: list[dict], batch_size: int = 100) -> int:
    """Store entities in database in batches."""
    stored = 0

    async with get_db_context() as db:
        for i in range(0, len(entities), batch_size):
            batch = entities[i : i + batch_size]

            for entity_data in batch:
                # Create entity
                entity = CarbonEntity(**entity_data)
                db.add(entity)

            await db.commit()
            stored += len(batch)

            print(f"  Stored {stored}/{len(entities)} entities...")

    return stored


async def discover_and_download_datasets():
    """Discover and download real datasets."""
    print("\n" + "=" * 80)
    print("Step 1: Discovering Real Carbon Datasets")
    print("=" * 80)

    downloaded_files = []

    async with FileDownloader() as downloader:
        # Download known high-value datasets
        print("\nDownloading known high-value datasets:")

        for dataset_id, url in DIRECT_DOWNLOAD_URLS.items():
            print(f"\n📥 Downloading: {dataset_id}")
            print(f"   URL: {url}")

            filepath = await downloader.download_file(url, max_size_mb=50)

            if filepath:
                downloaded_files.append((dataset_id, filepath))
                print(f"   ✅ Downloaded: {filepath.name}")
            else:
                print(f"   ❌ Failed to download")

        # Try to discover more from known dataset pages
        async with DatasetDiscovery() as discovery:
            for dataset_id, dataset_info in KNOWN_DATASETS.items():
                print(f"\n🔍 Discovering links from: {dataset_info['name']}")

                links = await discovery.extract_download_links(dataset_info["url"])

                if links:
                    print(f"   Found {len(links)} potential download links")

                    # Download first few promising links
                    for link in links[:3]:  # Limit to avoid overwhelming
                        if any(
                            pattern in link.lower()
                            for pattern in dataset_info["file_patterns"]
                        ):
                            print(f"   📥 Trying: {link}")

                            filepath = await downloader.download_file(
                                link, max_size_mb=100
                            )

                            if filepath:
                                downloaded_files.append((dataset_id, filepath))
                                print(f"   ✅ Downloaded: {filepath.name}")
                                break  # Got one, move to next dataset

    print(f"\n✅ Downloaded {len(downloaded_files)} files")
    return downloaded_files


async def parse_and_ingest_files(downloaded_files: list[tuple[str, Path]]):
    """Parse downloaded files and ingest into database."""
    print("\n" + "=" * 80)
    print("Step 2: Parsing Files and Building Taxonomy")
    print("=" * 80)

    parser = DataFileParser()
    all_entities = []
    parse_stats = {}

    for dataset_id, filepath in downloaded_files:
        print(f"\n📄 Parsing: {filepath.name}")

        # Register data source
        dataset_info = KNOWN_DATASETS.get(dataset_id, {})
        source_name = dataset_info.get("name", dataset_id)
        source_url = dataset_info.get("url", "")
        source_type = dataset_info.get("source_type", "government_database")

        source = await register_data_source(source_name, source_url, source_type)

        # Parse based on file extension
        entities = []

        if filepath.suffix.lower() in [".xlsx", ".xls"]:
            entities = await parser.parse_excel(filepath, source.name)
        elif filepath.suffix.lower() == ".csv":
            entities = await parser.parse_csv(filepath, source.name)
        elif filepath.suffix.lower() == ".xml":
            entities = await parser.parse_xml(filepath, source.name)

        if entities:
            # Add source UUID to all entities
            for entity in entities:
                entity["source_uuid"] = source.id

            all_entities.extend(entities)

            parse_stats[filepath.name] = {
                "entities_parsed": len(entities),
                "source": source.name,
            }

            print(f"   ✅ Parsed {len(entities)} entities")
        else:
            print(f"   ⚠️  No entities extracted")

    print(f"\n✅ Total entities parsed: {len(all_entities)}")
    return all_entities, parse_stats


async def analyze_discovered_taxonomy(entities: list[dict]):
    """Analyze taxonomy from discovered entities."""
    print("\n" + "=" * 80)
    print("Step 3: Analyzing Discovered Taxonomy")
    print("=" * 80)

    # Count by entity type
    by_type = {}
    by_category = {}
    by_geography = {}

    for entity in entities:
        entity_type = entity.get("entity_type", "unknown")
        by_type[entity_type] = by_type.get(entity_type, 0) + 1

        # Count categories
        for category in entity.get("category_hierarchy", []):
            by_category[category] = by_category.get(category, 0) + 1

        # Count geography
        for region in entity.get("geographic_scope", []):
            by_geography[region] = by_geography.get(region, 0) + 1

    print("\n📊 Entity Types:")
    for entity_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"   {entity_type}: {count:,}")

    print("\n🏷️  Top Categories:")
    for category, count in sorted(
        by_category.items(), key=lambda x: x[1], reverse=True
    )[:10]:
        print(f"   {category}: {count:,}")

    print("\n🌍 Geographic Coverage:")
    for region, count in sorted(
        by_geography.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"   {region}: {count:,}")


async def print_ingestion_summary(
    parse_stats: dict, stored_count: int, duration: float
):
    """Print comprehensive ingestion summary."""
    print("\n" + "=" * 80)
    print("📊 DEEP CRAWL INGESTION SUMMARY")
    print("=" * 80)

    print("\n┌─ Files Processed ────────────────────────────────────────────────┐")
    for filename, stats in parse_stats.items():
        print(f"│ ✅ {filename[:55]:<55} │")
        print(f"│    Source: {stats['source'][:50]:<50}   │")
        print(f"│    Entities: {stats['entities_parsed']:>6,}                                         │")
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Ingestion Statistics ───────────────────────────────────────────┐")
    print(f"│ Files Processed:              {len(parse_stats):>6}                            │")
    print(f"│ Entities Ingested:            {stored_count:>6,}                           │")
    print(f"│ Duration:                     {duration:>6.1f}s                          │")
    print(f"│ Rate:                         {stored_count/duration if duration > 0 else 0:>6.1f} entities/sec              │")
    print("└──────────────────────────────────────────────────────────────────┘")

    # Get database stats
    async with get_db_context() as db:
        total_stmt = select(func.count()).select_from(CarbonEntity)
        total = await db.scalar(total_stmt) or 0

        embedded_stmt = select(func.count()).select_from(CarbonEntity).where(
            CarbonEntity.embedding.is_not(None)
        )
        embedded = await db.scalar(embedded_stmt) or 0

    print("\n┌─ Database Status ────────────────────────────────────────────────┐")
    print(f"│ Total Entities in DB:         {total:>6,}                           │")
    print(f"│ Entities with Embeddings:     {embedded:>6,} ({embedded/total*100 if total > 0 else 0:>5.1f}%)                │")
    print(f"│ Entities Needing Embeddings:  {total - embedded:>6,}                           │")
    print("└──────────────────────────────────────────────────────────────────┘")


async def main():
    """Main execution."""
    print("=" * 80)
    print("MOTHRA - Deep Crawl Real Carbon Datasets")
    print("=" * 80)
    print("\nThis script discovers, downloads, and ingests REAL carbon emissions data")
    print("from government sources in Excel/XML/CSV formats.")

    start_time = datetime.now(UTC)

    # Initialize database
    print("\n🔧 Initializing database...")
    await init_db()
    print("✅ Database ready")

    # Step 1: Discover and download
    downloaded_files = await discover_and_download_datasets()

    if not downloaded_files:
        print("\n⚠️  No files downloaded. Check URLs and network connection.")
        return

    # Step 2: Parse and analyze
    entities, parse_stats = await parse_and_ingest_files(downloaded_files)

    if not entities:
        print("\n⚠️  No entities parsed from files.")
        return

    # Analyze taxonomy before storing
    await analyze_discovered_taxonomy(entities)

    # Step 3: Store in database
    print("\n" + "=" * 80)
    print("Step 4: Storing in Database")
    print("=" * 80)

    stored_count = await store_entities(entities, batch_size=100)

    # Final summary
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    await print_ingestion_summary(parse_stats, stored_count, duration)

    print("\n" + "=" * 80)
    print("🎉 Deep Crawl Complete!")
    print("=" * 80)

    print("\n📖 Next Steps:")
    print("1. Generate embeddings: python scripts/chunk_and_embed_all.py")
    print("2. Test semantic search on real data: python scripts/test_search.py")
    print(f"3. Explore {stored_count:,} real carbon entities in database")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
