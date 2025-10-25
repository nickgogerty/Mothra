"""
Test EC3 Integration.

Simple test to validate EC3 API connection and EPD import functionality.
Tests without requiring API key (public access).
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import func, select

from mothra.agents.discovery.ec3_integration import (
    EC3Client,
    EC3EPDParser,
    import_epds_from_ec3,
)
from mothra.db.models import CarbonEntity, DataSource
from mothra.db.models_verification import CarbonEntityVerification
from mothra.db.session import get_db_context, init_db
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


async def test_ec3_connection():
    """Test EC3 API connection."""
    print("\n" + "=" * 80)
    print("TEST 1: EC3 API Connection")
    print("=" * 80)

    async with EC3Client() as client:
        # Try searching for concrete EPDs
        result = await client.search_epds(category="Concrete", limit=5)

        if result and "results" in result:
            count = len(result.get("results", []))
            total = result.get("count", 0)
            print(f"✅ Successfully connected to EC3 API")
            print(f"   Retrieved {count} EPDs (total available: {total:,})")
            return True
        else:
            print(f"❌ Failed to connect to EC3 API")
            print(f"   Response: {result}")
            return False


async def test_epd_parsing():
    """Test EPD parsing logic."""
    print("\n" + "=" * 80)
    print("TEST 2: EPD Parsing")
    print("=" * 80)

    async with EC3Client() as client:
        # Get one concrete EPD
        result = await client.search_epds(category="Concrete", limit=1)

        if not result or "results" not in result or not result["results"]:
            print("❌ No EPDs found to test parsing")
            return False

        epd_data = result["results"][0]
        print(f"\nParsing EPD: {epd_data.get('name', 'Unknown')}")

        # Create data source
        async with get_db_context() as db:
            source_stmt = select(DataSource).where(
                DataSource.name == "EC3 Building Transparency"
            )
            result = await db.execute(source_stmt)
            source = result.scalar_one_or_none()

            if not source:
                source = DataSource(
                    name="EC3 Building Transparency",
                    source_type="api",
                    category="standards",  # Required field - EPD standards organization
                    url="https://openepd.buildingtransparency.org",
                    access_method="rest",  # Required field
                    data_format="json",
                    update_frequency="daily",
                    priority="high",
                    status="active",
                )
                db.add(source)
                await db.flush()

            # Parse EPD
            parser = EC3EPDParser()
            entity_dict, verification_dict = parser.parse_epd_to_entity(epd_data, source)

            print(f"\n✅ Successfully parsed EPD")
            print(f"   Name: {entity_dict.get('name')}")
            print(f"   Category: {entity_dict.get('category_hierarchy')}")
            print(f"   Entity Type: {entity_dict.get('entity_type')}")
            print(
                f"   LCA Stages: {verification_dict.get('lca_stages_included', [])}"
            )
            print(f"   EPD Number: {verification_dict.get('epd_registration_number')}")
            print(f"   Verified: {verification_dict.get('third_party_verified')}")

            return True


async def test_epd_import():
    """Test full EPD import pipeline."""
    print("\n" + "=" * 80)
    print("TEST 3: EPD Import Pipeline")
    print("=" * 80)

    # Get stats before
    async with get_db_context() as db:
        total_stmt = select(func.count()).select_from(CarbonEntity)
        total_before = await db.scalar(total_stmt) or 0

        verified_stmt = select(func.count()).select_from(CarbonEntityVerification)
        verified_before = await db.scalar(verified_stmt) or 0

    print(f"\nBefore import:")
    print(f"  Total entities: {total_before:,}")
    print(f"  Verified entities: {verified_before:,}")

    # Import 10 concrete EPDs
    print(f"\nImporting 10 Concrete EPDs from EC3...")
    result = await import_epds_from_ec3(category="Concrete", limit=10)

    print(f"\n✅ Import completed")
    print(f"   EPDs imported: {result['epds_imported']}")
    print(f"   Errors: {result['errors']}")

    # Get stats after
    async with get_db_context() as db:
        total_stmt = select(func.count()).select_from(CarbonEntity)
        total_after = await db.scalar(total_stmt) or 0

        verified_stmt = select(func.count()).select_from(CarbonEntityVerification)
        verified_after = await db.scalar(verified_stmt) or 0

    print(f"\nAfter import:")
    print(f"  Total entities: {total_after:,} (+{total_after - total_before})")
    print(
        f"  Verified entities: {verified_after:,} (+{verified_after - verified_before})"
    )

    return result["epds_imported"] > 0


async def test_verification_data():
    """Test verification data storage."""
    print("\n" + "=" * 80)
    print("TEST 4: Verification Data Storage")
    print("=" * 80)

    async with get_db_context() as db:
        # Get a verified entity
        stmt = (
            select(CarbonEntity, CarbonEntityVerification)
            .join(
                CarbonEntityVerification,
                CarbonEntity.id == CarbonEntityVerification.entity_id,
            )
            .where(CarbonEntityVerification.verification_status == "verified")
            .limit(1)
        )

        result = await db.execute(stmt)
        row = result.first()

        if not row:
            print("❌ No verified entities found")
            return False

        entity, verification = row

        print(f"\n✅ Found verified entity:")
        print(f"   Name: {entity.name}")
        print(f"   Source: {entity.source_id}")
        print(f"\n   Verification Details:")
        print(f"   - Status: {verification.verification_status}")
        print(f"   - Standards: {verification.verification_standards}")
        print(f"   - GHG Scopes: {verification.ghg_scopes}")
        print(f"   - LCA Stages: {verification.lca_stages_included}")
        print(f"   - EPD Number: {verification.epd_registration_number}")
        print(f"   - ISO 14067: {verification.iso_14067_compliant}")
        print(f"   - EN 15804: {verification.en_15804_compliant}")
        print(f"   - Third Party: {verification.third_party_verified}")

        if verification.lca_stage_emissions:
            print(f"\n   LCA Stage Emissions (kg CO2e):")
            for stage, value in verification.lca_stage_emissions.items():
                print(f"     {stage}: {value}")

        return True


async def main():
    """Run all tests."""
    print("=" * 80)
    print("EC3 INTEGRATION TEST SUITE")
    print("=" * 80)
    print("\nTesting EC3 (Embodied Carbon in Construction Calculator) integration")
    print("with Building Transparency's openEPD API")
    print("\nDatabase: 90,000+ verified construction material EPDs")

    # Check for API key
    import os

    if not os.getenv("EC3_API_KEY"):
        print("\n⚠️  EC3_API_KEY not set")
        print("   Using public access (limited)")
        print("   Get key at: https://buildingtransparency.org/ec3/manage-apps/keys")

    # Initialize database
    print("\n🔧 Initializing database...")
    await init_db()
    print("✅ Database ready")

    # Run tests
    tests = [
        ("EC3 Connection", test_ec3_connection),
        ("EPD Parsing", test_epd_parsing),
        ("EPD Import", test_epd_import),
        ("Verification Data", test_verification_data),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with error:")
            print(f"   {type(e).__name__}: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print()
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")

    print("\n" + "=" * 80)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 80)

    if passed == total:
        print("\n🎉 All tests passed! EC3 integration is working correctly.")
        print("\nNext steps:")
        print("1. Run: python scripts/import_ec3_epds.py")
        print("2. Import EPDs from multiple material categories")
        print("3. Generate embeddings for semantic search")
        print("4. Test search queries on construction materials")
    else:
        print(
            f"\n⚠️  {total - passed} test(s) failed. Check errors above for details."
        )

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
