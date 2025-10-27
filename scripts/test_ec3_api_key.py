"""
Quick EC3 API Key Test

Tests the EC3 API key by fetching a small sample of EPDs.
Verifies authentication works before running large bulk imports.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mothra.agents.discovery.ec3_integration import EC3Client
from mothra.config import settings


async def test_ec3_api():
    """Test EC3 API connection with authentication."""
    print("=" * 80)
    print("EC3 API KEY TEST")
    print("=" * 80)

    # Check if API key is configured
    if not settings.ec3_api_key:
        print("\n❌ EC3_API_KEY is NOT configured!")
        print("\nPlease set your API key in .env file:")
        print("   EC3_API_KEY=your-key-here")
        print("\nOr as environment variable:")
        print("   export EC3_API_KEY='your-key-here'")
        return False

    print(f"\n✅ EC3_API_KEY is configured")
    print(f"   Key: {settings.ec3_api_key[:10]}...{settings.ec3_api_key[-4:]}")

    # Test API connection
    print("\n🔍 Testing API connection...")
    print("   Endpoint: https://openepd.buildingtransparency.org/api")

    try:
        async with EC3Client() as client:
            # Try to fetch 5 concrete EPDs
            print("\n   Fetching 5 Concrete EPDs...")
            result = await client.search_epds(category="Concrete", limit=5)

            if result and "results" in result:
                epds = result.get("results", [])
                total = result.get("count", 0)

                print(f"\n✅ SUCCESS! API is working!")
                print(f"\n   Retrieved: {len(epds)} EPDs")
                print(f"   Available in Concrete category: {total:,}")

                if epds:
                    print(f"\n📦 Sample EPDs:")
                    for i, epd in enumerate(epds[:3], 1):
                        name = epd.get("name", "Unknown")
                        manufacturer = epd.get("manufacturer", {}).get(
                            "name", "Unknown"
                        )
                        print(f"   {i}. {name[:60]}")
                        print(f"      Manufacturer: {manufacturer}")

                print("\n" + "=" * 80)
                print("🎉 EC3 API KEY IS VALID!")
                print("=" * 80)

                print("\nEstimated EPDs available:")
                categories = {
                    "Concrete": 12000,
                    "Steel": 8000,
                    "Wood": 5000,
                    "Insulation": 3000,
                    "Glass": 2000,
                    "Aluminum": 2000,
                    "Gypsum": 1000,
                    "Roofing": 1500,
                    "Flooring": 1000,
                    "Sealants": 500,
                }

                total_estimated = sum(categories.values())
                print(f"\n   Total across all categories: ~{total_estimated:,} EPDs")

                for category, count in categories.items():
                    print(f"   • {category:20} ~{count:>6,} EPDs")

                print("\n📖 Next Steps:")
                print("   1. Run bulk import: python scripts/bulk_import_epds.py")
                print("   2. Import 9,290 per category to reach 100k total")
                print("   3. Duration: ~30-45 minutes for full import")

                return True

            else:
                print(f"\n⚠️  Unexpected response: {result}")
                return False

    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        print("\nPossible issues:")
        print("   • Invalid API key")
        print("   • Network connectivity")
        print("   • EC3 API service down")
        print("\nTroubleshooting:")
        print("   1. Verify key at: https://buildingtransparency.org/ec3/")
        print("   2. Check .env file has: EC3_API_KEY=your-key-here")
        print("   3. Try running: python scripts/check_ec3_key.py")
        return False


async def main():
    """Run API key test."""
    success = await test_ec3_api()

    if success:
        print()
        sys.exit(0)
    else:
        print("\n❌ API key test failed")
        print()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
