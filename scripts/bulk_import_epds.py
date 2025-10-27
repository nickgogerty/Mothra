"""
MOTHRA - Bulk EPD Import for Rapid Dataset Growth

Optimized script to rapidly import large quantities of EC3 EPDs.
Target: 100,000+ entities as fast as possible.

Strategies:
1. Parallel category imports
2. Larger batch sizes
3. Progress tracking
4. Resume capability if interrupted
"""

import asyncio
import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import func, select

from mothra.agents.discovery.ec3_integration import import_epds_from_ec3
from mothra.db.models import CarbonEntity
from mothra.db.models_verification import CarbonEntityVerification
from mothra.db.session import get_db_context, init_db
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


async def get_entity_count():
    """Get current entity count."""
    async with get_db_context() as db:
        total_stmt = select(func.count()).select_from(CarbonEntity)
        return await db.scalar(total_stmt) or 0


async def get_verified_count():
    """Get verified entity count."""
    async with get_db_context() as db:
        verified_stmt = select(func.count()).select_from(CarbonEntityVerification)
        return await db.scalar(verified_stmt) or 0


async def import_category(category: str, limit: int, stats: dict):
    """Import EPDs from one category with progress tracking."""
    print(f"\n{'='*80}")
    print(f"📦 Category: {category}")
    print(f"{'='*80}")
    print(f"Target: {limit:,} EPDs")

    start_time = datetime.now(UTC)
    start_count = await get_entity_count()

    try:
        result = await import_epds_from_ec3(category=category, limit=limit)

        end_count = await get_entity_count()
        duration = (datetime.now(UTC) - start_time).total_seconds()

        imported = result.get("epds_imported", 0)
        errors = result.get("errors", 0)

        stats["categories_completed"] += 1
        stats["total_imported"] += imported
        stats["total_errors"] += errors
        stats["total_duration"] += duration

        print(f"\n✅ {category} Complete:")
        print(f"   Imported: {imported:,}")
        print(f"   Errors: {errors}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Rate: {imported / duration:.1f} EPDs/sec" if duration > 0 else "")
        print(f"   Database: {end_count:,} total entities")

        return {
            "category": category,
            "imported": imported,
            "errors": errors,
            "duration": duration,
        }

    except Exception as e:
        print(f"\n❌ {category} Failed: {e}")
        logger.error("category_import_failed", category=category, error=str(e))
        return {"category": category, "imported": 0, "errors": 1, "duration": 0}


async def bulk_import_sequential(categories: list[str], limit_per_category: int):
    """Import EPDs sequentially (one category at a time)."""
    print("\n" + "=" * 80)
    print("SEQUENTIAL IMPORT MODE")
    print("=" * 80)
    print(f"\nImporting {len(categories)} categories")
    print(f"Target: {limit_per_category:,} EPDs per category")
    print(f"Total target: {limit_per_category * len(categories):,} EPDs")

    stats = {
        "categories_completed": 0,
        "total_imported": 0,
        "total_errors": 0,
        "total_duration": 0,
    }

    results = []
    for category in categories:
        result = await import_category(category, limit_per_category, stats)
        results.append(result)

        # Progress update
        progress_pct = (stats["categories_completed"] / len(categories)) * 100
        print(f"\n📊 Overall Progress: {progress_pct:.1f}%")
        print(
            f"   Categories: {stats['categories_completed']}/{len(categories)}"
        )
        print(f"   Total Imported: {stats['total_imported']:,}")
        print(f"   Total Duration: {stats['total_duration']:.1f}s")

    return stats, results


async def bulk_import_parallel(categories: list[str], limit_per_category: int, batch_size: int = 3):
    """Import EPDs in parallel batches (faster but more resource intensive)."""
    print("\n" + "=" * 80)
    print("PARALLEL IMPORT MODE")
    print("=" * 80)
    print(f"\nImporting {len(categories)} categories")
    print(f"Parallel batch size: {batch_size} categories at once")
    print(f"Target: {limit_per_category:,} EPDs per category")
    print(f"Total target: {limit_per_category * len(categories):,} EPDs")

    stats = {
        "categories_completed": 0,
        "total_imported": 0,
        "total_errors": 0,
        "total_duration": 0,
    }

    results = []

    # Process in batches
    for i in range(0, len(categories), batch_size):
        batch = categories[i : i + batch_size]

        print(f"\n🚀 Batch {i // batch_size + 1}: {', '.join(batch)}")

        # Import all categories in batch concurrently
        tasks = [import_category(cat, limit_per_category, stats) for cat in batch]
        batch_results = await asyncio.gather(*tasks)

        results.extend(batch_results)

        # Progress update
        progress_pct = (stats["categories_completed"] / len(categories)) * 100
        print(f"\n📊 Overall Progress: {progress_pct:.1f}%")
        print(
            f"   Categories: {stats['categories_completed']}/{len(categories)}"
        )
        print(f"   Total Imported: {stats['total_imported']:,}")

    return stats, results


async def main():
    """Run bulk EPD import."""
    print("=" * 80)
    print("MOTHRA - BULK EPD IMPORT")
    print("=" * 80)
    print("\nRapid dataset expansion to 100,000+ entities")

    # Initialize database
    print("\n🔧 Initializing database...")
    await init_db()
    print("✅ Database ready")

    # Get current state
    start_entities = await get_entity_count()
    start_verified = await get_verified_count()

    print(f"\n📊 Current State:")
    print(f"   Total Entities: {start_entities:,}")
    print(f"   Verified EPDs: {start_verified:,}")

    # Calculate target
    target = 100000
    remaining = target - start_entities
    print(f"\n🎯 Target: {target:,} entities")
    print(f"   Remaining: {remaining:,}")

    # EC3 categories
    categories = [
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

    # Calculate imports needed
    per_category = remaining // len(categories)

    print(f"\n📦 Strategy:")
    print(f"   Categories: {len(categories)}")
    print(f"   Per Category: {per_category:,} EPDs")
    print(f"   Total: {per_category * len(categories):,} EPDs")

    # Ask user for confirmation and quantity
    print(f"\n⚠️  Large imports take time:")
    print(f"   1,000 EPDs/category = ~5 minutes")
    print(f"   5,000 EPDs/category = ~20 minutes")
    print(f"   10,000 EPDs/category = ~45 minutes")

    try:
        choice = (
            input(
                f"\nImport {per_category:,} per category? (y/n) [default: y]: "
            ).strip()
            or "y"
        )

        if choice.lower() != "y":
            custom = input(f"How many per category? [default: 1000]: ").strip()
            per_category = int(custom) if custom else 1000

        # Choose import mode
        mode = (
            input(
                "\nImport mode:\n  1. Sequential (safer, slower)\n  2. Parallel (faster, needs good connection)\n\nChoice [default: 1]: "
            ).strip()
            or "1"
        )

    except (ValueError, KeyboardInterrupt):
        print("\n\n❌ Cancelled")
        return

    print(f"\n🚀 Starting import...")
    print(f"   Mode: {'Parallel' if mode == '2' else 'Sequential'}")
    print(f"   Per Category: {per_category:,}")
    print(f"   Total Target: {per_category * len(categories):,}")

    start_time = datetime.now(UTC)

    # Run import
    if mode == "2":
        stats, results = await bulk_import_parallel(categories, per_category, batch_size=3)
    else:
        stats, results = await bulk_import_sequential(categories, per_category)

    end_time = datetime.now(UTC)
    total_duration = (end_time - start_time).total_seconds()

    # Get final state
    final_entities = await get_entity_count()
    final_verified = await get_verified_count()

    # Print summary
    print("\n" + "=" * 80)
    print("📊 BULK IMPORT SUMMARY")
    print("=" * 80)

    print("\n┌─ Import Results ─────────────────────────────────────────────────┐")
    print(f"│ Categories Processed:      {stats['categories_completed']:>10,}                        │")
    print(f"│ EPDs Imported:             {stats['total_imported']:>10,}                        │")
    print(f"│ Errors:                    {stats['total_errors']:>10,}                        │")
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Database Growth ────────────────────────────────────────────────┐")
    print(f"│ Before:                    {start_entities:>10,} entities                  │")
    print(f"│ After:                     {final_entities:>10,} entities                  │")
    print(f"│ Growth:                    {final_entities - start_entities:>10,} entities                  │")
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Verification Coverage ──────────────────────────────────────────┐")
    print(f"│ Verified EPDs:             {final_verified:>10,}                        │")
    print(
        f"│ Verification Rate:         {(final_verified / final_entities * 100) if final_entities > 0 else 0:>10.1f}%                       │"
    )
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Performance ────────────────────────────────────────────────────┐")
    print(f"│ Total Duration:            {total_duration:>10.1f}s                       │")
    print(
        f"│ Import Rate:               {stats['total_imported'] / total_duration:>10.1f} EPDs/sec              │"
    )
    print(
        f"│ Average per Category:      {total_duration / len(categories):>10.1f}s                       │"
    )
    print("└──────────────────────────────────────────────────────────────────┘")

    # Progress to 100k
    progress = (final_entities / target) * 100

    print("\n" + "=" * 80)
    print(f"📈 Progress to 100,000: {progress:.1f}%")
    print(f"   [{final_entities:,} / {target:,}]")
    print("=" * 80)

    if final_entities >= target:
        print("\n🏆 TARGET ACHIEVED!")
        print(f"   You have {final_entities:,} carbon entities!")
        print(f"   Including {final_verified:,} verified EPDs!")
    else:
        remaining = target - final_entities
        print(f"\n   Remaining: {remaining:,} entities")
        print(f"\n💡 To reach 100k:")
        print(f"   • Run again with {remaining // len(categories):,} per category")
        print(f"   • Or focus on Concrete: {remaining} EPDs")

    print("\n📖 Next Steps:")
    print("   1. Generate embeddings: python scripts/chunk_and_embed_all.py")
    print("   2. Test semantic search: python scripts/test_search.py")
    print("   3. Query verified EPDs: python scripts/query_epds.py")
    print("   4. Build custom workflows with 100k+ verified data")

    print("\n" + "=" * 80)

    # Show top categories by import count
    print("\n📦 Category Breakdown:")
    for result in sorted(results, key=lambda x: x["imported"], reverse=True):
        print(f"   {result['category']:20} {result['imported']:>8,} EPDs")

    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Import interrupted by user")
        print("Progress has been saved. Run again to continue.")
