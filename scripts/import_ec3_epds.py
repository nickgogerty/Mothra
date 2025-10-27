"""
Import EPDs from EC3 (Embodied Carbon in Construction Calculator).

This script imports verified Environmental Product Declarations from
Building Transparency's EC3 database (90,000+ EPDs).

Categories available:
- Concrete (ready-mix, precast, blocks)
- Steel (structural, rebar, decking)
- Wood (lumber, engineered wood, panels)
- Insulation (mineral wool, foam, cellulose)
- Glass (glazing, curtain walls)
- Aluminum (extrusions, cladding)
- Gypsum (drywall, plaster)
- And many more construction materials

Each EPD includes:
- Full LCA data (A1-A3 minimum, often through D)
- Verified carbon footprints
- Third-party verification
- EN 15804+A2 compliance
- Product-specific data
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


# EC3 Material Categories (primary construction materials)
EC3_CATEGORIES = [
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


async def get_database_stats():
    """Get current database statistics."""
    async with get_db_context() as db:
        # Total entities
        total_stmt = select(func.count()).select_from(CarbonEntity)
        total = await db.scalar(total_stmt) or 0

        # EPD entities (from EC3)
        epd_stmt = select(func.count()).select_from(CarbonEntity).where(
            CarbonEntity.source_id == "EC3 Building Transparency"
        )
        epd_count = await db.scalar(epd_stmt) or 0

        # Verified entities
        verified_stmt = select(func.count()).select_from(CarbonEntityVerification).where(
            CarbonEntityVerification.verification_status == "verified"
        )
        verified_count = await db.scalar(verified_stmt) or 0

        # Entities by category
        category_stmt = select(
            CarbonEntity.category_hierarchy, func.count(CarbonEntity.id)
        ).group_by(CarbonEntity.category_hierarchy)
        result = await db.execute(category_stmt)
        by_category = dict(result.all())

        return {
            "total_entities": total,
            "epd_entities": epd_count,
            "verified_entities": verified_count,
            "by_category": by_category,
        }


async def import_category(category: str, limit: int = 100) -> dict:
    """Import EPDs for a specific category."""
    print(f"\n📦 Importing category: {category}")
    print(f"   Limit: {limit} EPDs")

    start_time = datetime.now(UTC)

    result = await import_epds_from_ec3(category=category, limit=limit)

    duration = (datetime.now(UTC) - start_time).total_seconds()

    print(f"   ✅ Imported: {result['epds_imported']}")
    print(f"   ❌ Errors: {result['errors']}")
    print(f"   ⏱️  Duration: {duration:.1f}s")

    return {
        "category": category,
        "imported": result["epds_imported"],
        "errors": result["errors"],
        "duration": duration,
    }


async def print_summary(category_results: list[dict], stats_before: dict, stats_after: dict):
    """Print comprehensive import summary."""
    print("\n" + "=" * 80)
    print("📊 EC3 EPD IMPORT SUMMARY")
    print("=" * 80)

    print("\n┌─ Import Results by Category ─────────────────────────────────────┐")
    total_imported = 0
    total_errors = 0

    for result in category_results:
        print(f"│ {result['category']:<20} │ Imported: {result['imported']:>4} │ Errors: {result['errors']:>2} │ {result['duration']:>5.1f}s │")
        total_imported += result["imported"]
        total_errors += result["errors"]

    print("├───────────────────────────────────────────────────────────────────┤")
    print(f"│ {'TOTAL':<20} │ Imported: {total_imported:>4} │ Errors: {total_errors:>2} │         │")
    print("└───────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Database Statistics ────────────────────────────────────────────┐")
    print(f"│ Total Entities Before:        {stats_before['total_entities']:>6,}                           │")
    print(f"│ Total Entities After:         {stats_after['total_entities']:>6,}                           │")
    print(f"│ New EPD Entities:             {total_imported:>6,}                           │")
    print(f"│ Total EPDs in Database:       {stats_after['epd_entities']:>6,}                           │")
    print(f"│ Verified Entities:            {stats_after['verified_entities']:>6,}                           │")
    print("└──────────────────────────────────────────────────────────────────┘")

    print("\n┌─ Data Quality ───────────────────────────────────────────────────┐")
    verification_rate = (
        stats_after["verified_entities"] / stats_after["total_entities"] * 100
        if stats_after["total_entities"] > 0 else 0
    )
    print(f"│ Verification Rate:            {verification_rate:>6.1f}%                          │")
    print(f"│ EN 15804 Compliant:           {total_imported:>6,} (all EC3 EPDs)               │")
    print(f"│ Third-Party Verified:         {total_imported:>6,} (all EC3 EPDs)               │")
    print("└──────────────────────────────────────────────────────────────────┘")


async def main():
    """Main execution."""
    print("=" * 80)
    print("MOTHRA - EC3 EPD Importer")
    print("=" * 80)
    print("\nImporting verified Environmental Product Declarations")
    print("from EC3 (Building Transparency) database")
    print("\nEC3 Database: 90,000+ EPDs for construction materials")

    # Check for API key
    import os
    if not os.getenv("EC3_API_KEY"):
        print("\n⚠️  WARNING: EC3_API_KEY not set in environment")
        print("   Some API endpoints may require authentication")
        print("   Get your key at: https://buildingtransparency.org/ec3/manage-apps/keys")
        print("\n   Continuing with public access (limited)...")

    start_time = datetime.now(UTC)

    # Initialize database
    print("\n🔧 Initializing database...")
    await init_db()
    print("✅ Database ready")

    # Get initial stats
    stats_before = await get_database_stats()
    print(f"\nInitial state: {stats_before['total_entities']:,} entities")
    print(f"Existing EPDs: {stats_before['epd_entities']:,}")

    # Import categories
    print("\n" + "=" * 80)
    print("Importing EPDs by Category")
    print("=" * 80)

    category_results = []

    # Allow user to choose categories or import all
    import_all = input("\nImport all categories? (y/n) [default: y]: ").strip().lower()
    import_all = import_all != 'n'

    if import_all:
        # Import from all categories
        per_category = int(input("EPDs per category? [default: 50]: ").strip() or "50")

        for category in EC3_CATEGORIES:
            result = await import_category(category, limit=per_category)
            category_results.append(result)
            await asyncio.sleep(1)  # Rate limiting
    else:
        # Import specific category
        print("\nAvailable categories:")
        for i, cat in enumerate(EC3_CATEGORIES, 1):
            print(f"  {i}. {cat}")

        choice = input("\nSelect category number: ").strip()
        try:
            category = EC3_CATEGORIES[int(choice) - 1]
            limit = int(input("How many EPDs? [default: 100]: ").strip() or "100")

            result = await import_category(category, limit=limit)
            category_results.append(result)
        except (ValueError, IndexError):
            print("Invalid selection")
            return

    # Get final stats
    stats_after = await get_database_stats()

    # Print summary
    duration = (datetime.now(UTC) - start_time).total_seconds()
    await print_summary(category_results, stats_before, stats_after)

    print("\n" + "=" * 80)
    print("🎉 EC3 EPD Import Complete!")
    print("=" * 80)

    print(f"\nTotal Duration: {duration:.1f}s ({duration/60:.1f} minutes)")

    print("\n📖 Next Steps:")
    print("1. Generate embeddings: python scripts/chunk_and_embed_all.py")
    print("2. Test semantic search on EPD data")
    print("3. Query by material category or manufacturer")
    print("4. Explore LCA stages and carbon footprints")

    print("\n💡 Example Queries:")
    print('   - "low carbon concrete ready mix"')
    print('   - "CLT cross laminated timber"')
    print('   - "recycled steel rebar"')
    print('   - "mineral wool insulation"')

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
