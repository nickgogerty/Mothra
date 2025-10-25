"""
MOTHRA - Mega Crawl Script

Comprehensive data ingestion combining:
1. Deep crawl of government datasets (EPA, DEFRA, EU ETS)
2. EC3 EPD database (90,000+ construction materials)
3. Additional research datasets
4. WebSearch-driven discovery

Target: 100,000+ carbon entities from verified sources
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
    KNOWN_DATASETS,
    DataFileParser,
    DatasetDiscovery,
    FileDownloader,
)
from mothra.agents.discovery.ec3_integration import import_epds_from_ec3
from mothra.db.models import CarbonEntity, DataSource
from mothra.db.models_verification import CarbonEntityVerification
from mothra.db.session import get_db_context, init_db
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


# Enhanced dataset catalog with more sources
MEGA_DATASETS = {
    **KNOWN_DATASETS,  # Include existing datasets
    # Additional government datasets
    "AUSTRALIA_NGER_2023": {
        "name": "Australia NGER Emissions Data",
        "url": "https://www.industry.gov.au/regulations-and-standards/national-greenhouse-and-energy-reporting-scheme/published-information",
        "file_patterns": ["nger", "emissions", ".xlsx", ".csv"],
        "format": "excel",
        "entity_type": "facility",
    },
    "CANADA_GHGRP_2023": {
        "name": "Canada GHG Reporting Program",
        "url": "https://open.canada.ca/data/en/dataset/a8ba14b7-7f23-462a-bdbb-83b0ef629823",
        "file_patterns": ["ghg", "facility", ".csv"],
        "format": "csv",
        "entity_type": "facility",
    },
    "JAPAN_GHG_INVENTORY": {
        "name": "Japan National GHG Inventory",
        "url": "https://www.nies.go.jp/gio/en/archive/nir/index.html",
        "file_patterns": ["inventory", ".xlsx"],
        "format": "excel",
        "entity_type": "process",
    },
    # Research datasets
    "EXIOBASE_3": {
        "name": "EXIOBASE 3 - Multi-Regional Input-Output Database",
        "url": "https://zenodo.org/records/5589597",
        "file_patterns": ["exiobase", ".csv", ".xlsx"],
        "format": "excel",
        "entity_type": "process",
    },
    "USEEIO_2": {
        "name": "USEEIO 2.0 - US Environmental Input-Output Model",
        "url": "https://www.epa.gov/land-research/us-environmentally-extended-input-output-useeio-models",
        "file_patterns": ["useeio", ".csv"],
        "format": "csv",
        "entity_type": "process",
    },
}


async def register_data_source(
    name: str, url: str, source_type: str, category: str = "government"
) -> DataSource:
    """Register a data source in the database."""
    async with get_db_context() as db:
        stmt = select(DataSource).where(DataSource.name == name)
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()

        if source:
            return source

        source = DataSource(
            name=name,
            source_type=source_type,
            category=category,
            url=url,
            access_method="file_download",
            update_frequency="annual",
            priority="high",
            extra_metadata={
                "discovered_by": "mega_crawl",
                "discovery_date": datetime.now(UTC).isoformat(),
            },
        )

        db.add(source)
        await db.commit()
        await db.refresh(source)

        logger.info("data_source_registered", name=name, url=url, category=category)
        return source


async def store_entities(entities: list[dict], batch_size: int = 100) -> int:
    """Store entities in database in batches."""
    stored = 0

    async with get_db_context() as db:
        for i in range(0, len(entities), batch_size):
            batch = entities[i : i + batch_size]

            for entity_data in batch:
                entity = CarbonEntity(**entity_data)
                db.add(entity)

            await db.commit()
            stored += len(batch)

            if stored % 500 == 0 or stored == len(entities):
                print(f"  Stored {stored:,}/{len(entities):,} entities...")

    return stored


async def crawl_government_datasets():
    """Crawl government datasets (EPA, DEFRA, EU ETS, etc.)."""
    print("\n" + "=" * 80)
    print("Phase 1: Government Datasets")
    print("=" * 80)

    downloaded_files = []
    stats = {"files": 0, "entities": 0, "sources": 0}

    async with FileDownloader() as downloader:
        async with DatasetDiscovery() as discovery:
            for dataset_id, dataset_info in MEGA_DATASETS.items():
                print(f"\n🔍 Discovering: {dataset_info['name']}")

                links = await discovery.extract_download_links(dataset_info["url"])

                if links:
                    print(f"   Found {len(links)} potential files")

                    # Download first 3 promising links
                    for link in links[:3]:
                        # Check if matches file patterns
                        if any(
                            pattern in link.lower()
                            for pattern in dataset_info.get("file_patterns", [])
                        ):
                            print(f"   📥 Downloading: {Path(link).name[:60]}...")
                            filepath = await downloader.download_file(link, max_size_mb=100)

                            if filepath:
                                downloaded_files.append(
                                    (dataset_info["name"], dataset_info["url"], filepath)
                                )
                                stats["files"] += 1
                                print(f"   ✅ {filepath.name}")

    # Parse downloaded files
    if downloaded_files:
        print(f"\n📊 Parsing {len(downloaded_files)} files...")
        parser = DataFileParser()

        for source_name, source_url, filepath in downloaded_files:
            print(f"\n📄 {filepath.name}")

            # Register source
            source = await register_data_source(
                source_name, source_url, "government_database", "government"
            )
            stats["sources"] += 1

            # Parse based on file type
            if filepath.suffix in [".xlsx", ".xls"]:
                entities = await parser.parse_excel(filepath, source_name)
            elif filepath.suffix == ".csv":
                entities = await parser.parse_csv(filepath, source_name)
            elif filepath.suffix == ".zip":
                # Try to extract and parse
                print("   ⚠️  ZIP file - attempting extraction...")
                entities = await parser.parse_zip(filepath, source_name)
            else:
                entities = []

            if entities:
                # Add source_id
                for entity in entities:
                    entity["source_id"] = source.id

                # Store
                stored = await store_entities(entities)
                stats["entities"] += stored
                print(f"   ✅ Stored {stored:,} entities")

    return stats


async def import_ec3_epds_multi_category(categories: list[str], limit_per_category: int):
    """Import EPDs from EC3 across multiple categories."""
    print("\n" + "=" * 80)
    print("Phase 2: EC3 Construction Material EPDs")
    print("=" * 80)

    total_imported = 0
    total_errors = 0

    for category in categories:
        print(f"\n📦 Importing {category} EPDs (limit: {limit_per_category})...")

        try:
            result = await import_epds_from_ec3(category=category, limit=limit_per_category)

            imported = result.get("epds_imported", 0)
            errors = result.get("errors", 0)

            total_imported += imported
            total_errors += errors

            print(f"   ✅ Imported: {imported:,}")
            if errors:
                print(f"   ⚠️  Errors: {errors}")

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            logger.error("ec3_import_failed", category=category, error=str(e))

    return {"epds_imported": total_imported, "errors": total_errors}


async def get_database_stats():
    """Get comprehensive database statistics."""
    async with get_db_context() as db:
        # Total entities
        total_stmt = select(func.count()).select_from(CarbonEntity)
        total = await db.scalar(total_stmt) or 0

        # With embeddings
        embedded_stmt = select(func.count()).select_from(CarbonEntity).where(
            CarbonEntity.embedding.is_not(None)
        )
        embedded = await db.scalar(embedded_stmt) or 0

        # Verified entities (with EPD data)
        verified_stmt = select(func.count()).select_from(CarbonEntityVerification)
        verified = await db.scalar(verified_stmt) or 0

        # By entity type
        type_stmt = select(
            CarbonEntity.entity_type, func.count(CarbonEntity.id)
        ).group_by(CarbonEntity.entity_type)
        result = await db.execute(type_stmt)
        by_type = {row[0]: row[1] for row in result}

        # Data sources
        sources_stmt = select(func.count()).select_from(DataSource)
        sources = await db.scalar(sources_stmt) or 0

        return {
            "total_entities": total,
            "with_embeddings": embedded,
            "verified_entities": verified,
            "by_type": by_type,
            "data_sources": sources,
        }


async def main():
    """Run comprehensive mega crawl."""
    print("=" * 80)
    print("MOTHRA - MEGA CRAWL")
    print("=" * 80)
    print("\nComprehensive carbon data ingestion from:")
    print("  • Government datasets (EPA, DEFRA, EU ETS, Australia, Canada, Japan)")
    print("  • EC3 EPD database (90,000+ construction materials)")
    print("  • Research datasets (EXIOBASE, USEEIO)")
    print("\nTarget: 100,000+ verified carbon entities")

    # Initialize database
    print("\n🔧 Initializing database...")
    await init_db()
    print("✅ Database ready")

    # Get initial stats
    initial_stats = await get_database_stats()
    print(f"\n📊 Starting state: {initial_stats['total_entities']:,} entities")

    start_time = datetime.now(UTC)

    # Phase 1: Government datasets
    print("\n" + "=" * 80)
    gov_stats = await crawl_government_datasets()
    print(f"\n✅ Government phase complete:")
    print(f"   Files: {gov_stats['files']}")
    print(f"   Entities: {gov_stats['entities']:,}")
    print(f"   Sources: {gov_stats['sources']}")

    # Phase 2: EC3 EPDs
    print("\n" + "=" * 80)

    # EC3 categories to import
    ec3_categories = [
        "Concrete",
        "Steel",
        "Wood",
        "Insulation",
        "Glass",
        "Aluminum",
        "Gypsum",
        "Roofing",
        "Flooring",
        "Sealants",
    ]

    # Ask user how many EPDs per category
    print(f"\nEC3 has 10 material categories with 90,000+ total EPDs")
    print(f"Categories: {', '.join(ec3_categories)}")
    print(f"\nRecommended limits:")
    print(f"  • Quick test: 10-50 per category (100-500 total)")
    print(f"  • Medium: 100-500 per category (1,000-5,000 total)")
    print(f"  • Large: 1,000+ per category (10,000+ total)")
    print(f"  • Maximum: unlimited (90,000+ total, ~30 min)")

    try:
        limit_input = input(f"\nEPDs per category? [default: 100]: ").strip()
        limit_per_category = int(limit_input) if limit_input else 100
    except ValueError:
        limit_per_category = 100

    ec3_stats = await import_ec3_epds_multi_category(ec3_categories, limit_per_category)

    print(f"\n✅ EC3 phase complete:")
    print(f"   EPDs imported: {ec3_stats['epds_imported']:,}")
    print(f"   Categories: {len(ec3_categories)}")

    # Get final stats
    final_stats = await get_database_stats()
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    # Summary
    print("\n" + "=" * 80)
    print("📊 MEGA CRAWL SUMMARY")
    print("=" * 80)

    print("\n┌─ Ingestion Results ──────────────────────────────────────────────┐")
    print(f"│ Government Entities:       {gov_stats['entities']:>10,}                        │")
    print(f"│ EC3 EPDs:                  {ec3_stats['epds_imported']:>10,}                        │")
    print(f"│ ─────────────────────────────────────────────────────────────── │")
    print(
        f"│ Total New Entities:        {final_stats['total_entities'] - initial_stats['total_entities']:>10,}                        │"
    )
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Database Status ────────────────────────────────────────────────┐")
    print(f"│ Total Entities:            {final_stats['total_entities']:>10,}                        │")
    print(f"│ Verified (EPD):            {final_stats['verified_entities']:>10,}                        │")
    print(f"│ With Embeddings:           {final_stats['with_embeddings']:>10,}                        │")
    print(
        f"│ Data Sources:              {final_stats['data_sources']:>10,}                        │"
    )
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Entity Breakdown ───────────────────────────────────────────────┐")
    for entity_type, count in sorted(
        final_stats["by_type"].items(), key=lambda x: x[1], reverse=True
    ):
        print(f"│ {entity_type:30} {count:>10,}                        │")
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Performance ────────────────────────────────────────────────────┐")
    print(f"│ Duration:                  {duration:>10.1f}s                       │")
    print(
        f"│ Rate:                      {(final_stats['total_entities'] - initial_stats['total_entities']) / duration:>10,.1f} entities/sec           │"
    )
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n" + "=" * 80)
    print("🎉 MEGA CRAWL COMPLETE!")
    print("=" * 80)

    # Show progress towards 100k goal
    progress_pct = (final_stats["total_entities"] / 100000) * 100

    print(f"\n📈 Progress to 100,000 entities: {progress_pct:.1f}%")
    print(f"   [{final_stats['total_entities']:,} / 100,000]")

    if final_stats["total_entities"] >= 100000:
        print("\n🏆 TARGET ACHIEVED! You have 100,000+ carbon entities!")
    else:
        remaining = 100000 - final_stats["total_entities"]
        print(f"\n   Remaining: {remaining:,} entities")
        print(f"\n💡 To reach 100k:")
        print(
            f"   • Import more EPDs: {remaining // 10} per category × 10 categories"
        )
        print(f"   • Or import {remaining} from largest category (Concrete)")

    print("\n📖 Next Steps:")
    print("   1. Generate embeddings: python scripts/chunk_and_embed_all.py")
    print("   2. Test semantic search: python scripts/test_search.py")
    print("   3. Query verified EPDs: python scripts/query_epds.py")
    print("   4. Export to CSV: python scripts/export_entities.py")

    print()


if __name__ == "__main__":
    asyncio.run(main())
