"""
Alternative Dataset Growth Strategy (No EC3 API Key Required)

Expands dataset using government and research sources that don't require API keys.
Target: 50,000+ entities from freely accessible sources.
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
)
from mothra.db.models import CarbonEntity, DataSource
from mothra.db.session import get_db_context, init_db
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


# Expanded government datasets (no API key required)
GOVERNMENT_DATASETS = {
    "EPA_GHGRP_FULL": {
        "name": "EPA GHGRP Full Dataset 2023",
        "url": "https://www.epa.gov/ghgreporting/data-sets",
        "description": "Complete facility-level emissions",
        "expected_entities": 50000,
    },
    "EPA_FLIGHT": {
        "name": "EPA FLIGHT Tool Data",
        "url": "https://www.epa.gov/landfills/landfill-technical-data",
        "description": "Landfill emissions model data",
        "expected_entities": 2000,
    },
    "EIA_EMISSIONS": {
        "name": "EIA Energy-Related CO2 Emissions",
        "url": "https://www.eia.gov/environment/emissions/state/",
        "description": "State-level energy emissions",
        "expected_entities": 5000,
    },
    "UK_DEFRA_FULL": {
        "name": "UK DEFRA Full Conversion Factors 2024",
        "url": "https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024",
        "description": "Complete UK emission factors",
        "expected_entities": 3000,
    },
    "EU_ETS_FULL": {
        "name": "EU ETS Complete Database",
        "url": "https://www.eea.europa.eu/data-and-maps/data/european-union-emissions-trading-scheme-17",
        "description": "All EU facility emissions",
        "expected_entities": 15000,
    },
}


async def get_entity_count():
    """Get current entity count."""
    async with get_db_context() as db:
        total_stmt = select(func.count()).select_from(CarbonEntity)
        return await db.scalar(total_stmt) or 0


async def register_source(name: str, url: str, category: str = "government") -> DataSource:
    """Register data source."""
    async with get_db_context() as db:
        stmt = select(DataSource).where(DataSource.name == name)
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()

        if source:
            return source

        source = DataSource(
            name=name,
            source_type="government_database",
            category=category,
            url=url,
            access_method="file_download",
            update_frequency="annual",
            priority="high",
            extra_metadata={
                "discovered_by": "expand_without_ec3",
                "discovery_date": datetime.now(UTC).isoformat(),
            },
        )
        db.add(source)
        await db.commit()
        await db.refresh(source)

        return source


async def store_entities(entities: list[dict], batch_size: int = 500) -> int:
    """Store entities in database."""
    stored = 0

    async with get_db_context() as db:
        for i in range(0, len(entities), batch_size):
            batch = entities[i : i + batch_size]

            for entity_data in batch:
                entity = CarbonEntity(**entity_data)
                db.add(entity)

            await db.commit()
            stored += len(batch)

            if stored % 1000 == 0 or stored == len(entities):
                print(f"  💾 Stored {stored:,}/{len(entities):,} entities...")

    return stored


async def crawl_government_sources():
    """Crawl all available government sources."""
    print("\n" + "=" * 80)
    print("GOVERNMENT DATA COLLECTION")
    print("=" * 80)
    print("\nDiscovering and downloading files from public sources...")

    stats = {
        "files_downloaded": 0,
        "files_parsed": 0,
        "entities_ingested": 0,
        "sources_added": 0,
    }

    async with FileDownloader() as downloader:
        async with DatasetDiscovery() as discovery:
            for dataset_id, dataset_info in GOVERNMENT_DATASETS.items():
                print(f"\n{'─' * 80}")
                print(f"📊 {dataset_info['name']}")
                print(f"   Expected: ~{dataset_info['expected_entities']:,} entities")
                print(f"{'─' * 80}")

                # Discover download links
                links = await discovery.extract_download_links(dataset_info["url"])

                if not links:
                    print("   ⚠️  No downloadable files found")
                    continue

                print(f"   Found {len(links)} potential files")

                # Download promising files (Excel, CSV, ZIP)
                downloaded_files = []
                for link in links[:5]:  # Limit to 5 per source
                    if any(
                        ext in link.lower()
                        for ext in [".xlsx", ".xls", ".csv", ".zip"]
                    ):
                        filename = Path(link).name[:60]
                        print(f"   📥 Downloading: {filename}...")

                        filepath = await downloader.download_file(link, max_size_mb=200)

                        if filepath:
                            downloaded_files.append(filepath)
                            stats["files_downloaded"] += 1
                            print(f"      ✅ {filepath.name}")

                # Parse downloaded files
                if downloaded_files:
                    parser = DataFileParser()

                    for filepath in downloaded_files:
                        print(f"\n   📄 Parsing: {filepath.name}")

                        # Register source
                        source = await register_source(
                            dataset_info["name"],
                            dataset_info["url"],
                            "government",
                        )
                        stats["sources_added"] += 1

                        # Parse based on file type
                        entities = []
                        if filepath.suffix.lower() in [".xlsx", ".xls"]:
                            entities = await parser.parse_excel(
                                filepath, dataset_info["name"]
                            )
                        elif filepath.suffix.lower() == ".csv":
                            entities = await parser.parse_csv(
                                filepath, dataset_info["name"]
                            )
                        elif filepath.suffix.lower() == ".zip":
                            entities = await parser.parse_zip(
                                filepath, dataset_info["name"]
                            )

                        if entities:
                            # Add source UUID
                            for entity in entities:
                                entity["source_uuid"] = source.id

                            # Store
                            stored = await store_entities(entities)
                            stats["entities_ingested"] += stored
                            stats["files_parsed"] += 1
                            print(f"      ✅ Ingested {stored:,} entities")

    return stats


async def main():
    """Run alternative growth strategy."""
    print("=" * 80)
    print("MOTHRA - ALTERNATIVE DATASET GROWTH")
    print("=" * 80)
    print("\nGrow dataset using government sources (no EC3 API key required)")
    print("\nTarget: 50,000+ entities from:")
    print("  • EPA GHGRP (facility emissions)")
    print("  • EU ETS (European facilities)")
    print("  • UK DEFRA (emission factors)")
    print("  • EIA (energy emissions)")
    print("  • EPA FLIGHT (landfill data)")

    # Initialize
    print("\n🔧 Initializing database...")
    await init_db()
    print("✅ Database ready")

    # Get starting count
    start_count = await get_entity_count()
    print(f"\n📊 Starting count: {start_count:,} entities")

    start_time = datetime.now(UTC)

    # Crawl government sources
    stats = await crawl_government_sources()

    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    # Get final count
    final_count = await get_entity_count()

    # Print summary
    print("\n" + "=" * 80)
    print("📊 INGESTION SUMMARY")
    print("=" * 80)

    print("\n┌─ Files Processed ────────────────────────────────────────────────┐")
    print(f"│ Downloaded:                {stats['files_downloaded']:>10,}                        │")
    print(f"│ Parsed:                    {stats['files_parsed']:>10,}                        │")
    print(f"│ Sources Added:             {stats['sources_added']:>10,}                        │")
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Database Growth ────────────────────────────────────────────────┐")
    print(f"│ Before:                    {start_count:>10,} entities                  │")
    print(f"│ After:                     {final_count:>10,} entities                  │")
    print(f"│ Growth:                    {final_count - start_count:>10,} entities                  │")
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Performance ────────────────────────────────────────────────────┐")
    print(f"│ Duration:                  {duration:>10.1f}s                       │")
    print(
        f"│ Rate:                      {(final_count - start_count) / duration if duration > 0 else 0:>10.1f} entities/sec           │"
    )
    print("└──────────────────────────────────────────────────────────────────┘")

    # Progress
    progress = (final_count / 100000) * 100
    print("\n" + "=" * 80)
    print(f"📈 Progress to 100,000: {progress:.1f}%")
    print(f"   [{final_count:,} / 100,000]")
    print("=" * 80)

    if final_count >= 100000:
        print("\n🏆 TARGET ACHIEVED!")
        print(f"   You have {final_count:,} entities!")
    else:
        remaining = 100000 - final_count
        print(f"\n   Remaining: {remaining:,} entities")
        print("\n💡 Next steps to reach 100k:")
        print("   1. Get EC3 API key (free): https://buildingtransparency.org/ec3/")
        print("   2. Set key: export EC3_API_KEY='your-key'")
        print("   3. Run: python scripts/bulk_import_epds.py")
        print(f"   4. Import ~{remaining // 10:,} EPDs per category")

    print("\n📖 Available now:")
    print("   1. Generate embeddings: python scripts/chunk_and_embed_all.py")
    print("   2. Test semantic search: python scripts/test_search.py")
    print("   3. Query entities: python scripts/query_entities.py")

    print()


if __name__ == "__main__":
    asyncio.run(main())
