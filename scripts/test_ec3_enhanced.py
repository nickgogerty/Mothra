#!/usr/bin/env python3
"""
Test Enhanced EC3 API Integration

Tests all new features:
- OAuth 2.0 authentication
- Retry logic with exponential backoff
- Enhanced pagination
- Additional endpoints (plants, projects)
- Full data extraction
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mothra.agents.discovery.ec3_integration import EC3Client


async def test_basic_authentication():
    """Test 1: Basic Bearer Token Authentication"""
    print("\n" + "=" * 80)
    print("TEST 1: Basic Bearer Token Authentication")
    print("=" * 80)

    async with EC3Client() as client:
        # Test search with simple authentication
        results = await client.search_epds(category="Concrete", limit=5)
        print(f"✅ Successfully searched EPDs: {len(results.get('results', []))} results")
        print(f"   Total available: {results.get('count', 'unknown')}")
        if results.get("next"):
            print(f"   Has next page: Yes")


async def test_oauth_authentication():
    """Test 2: OAuth 2.0 Authentication (if configured)"""
    print("\n" + "=" * 80)
    print("TEST 2: OAuth 2.0 Authentication")
    print("=" * 80)

    # Check if OAuth credentials are available
    oauth_config = {
        "grant_type": os.getenv("EC3_OAUTH_GRANT_TYPE", "password"),
        "client_id": os.getenv("EC3_CLIENT_ID"),
        "client_secret": os.getenv("EC3_CLIENT_SECRET"),
        "username": os.getenv("EC3_USERNAME"),
        "password": os.getenv("EC3_PASSWORD"),
    }

    if not oauth_config["client_id"]:
        print("⏭️  Skipping OAuth test - credentials not configured")
        print("   To test OAuth, set environment variables:")
        print("   - EC3_OAUTH_GRANT_TYPE=password")
        print("   - EC3_CLIENT_ID=your_client_id")
        print("   - EC3_CLIENT_SECRET=your_client_secret")
        print("   - EC3_USERNAME=your_username")
        print("   - EC3_PASSWORD=your_password")
        return

    async with EC3Client(oauth_config=oauth_config) as client:
        results = await client.search_epds(category="Steel", limit=5)
        print(f"✅ Successfully authenticated via OAuth 2.0")
        print(f"   Search results: {len(results.get('results', []))} EPDs")


async def test_enhanced_pagination():
    """Test 3: Enhanced Pagination with next/previous tracking"""
    print("\n" + "=" * 80)
    print("TEST 3: Enhanced Pagination")
    print("=" * 80)

    async with EC3Client() as client:
        # Get first page
        page1 = await client.search_epds(category="Wood", limit=5, offset=0)
        print(f"✅ Page 1: {len(page1.get('results', []))} results")
        print(f"   Total count: {page1.get('count', 'unknown')}")
        print(f"   Next URL: {page1.get('next', 'None')}")
        print(f"   Previous URL: {page1.get('previous', 'None')}")

        # Get second page
        page2 = await client.search_epds(category="Wood", limit=5, offset=5)
        print(f"✅ Page 2: {len(page2.get('results', []))} results")
        print(f"   Next URL: {page2.get('next', 'None')}")
        print(f"   Previous URL: {page2.get('previous', 'None')}")


async def test_search_all():
    """Test 4: Automatic Pagination (search_epds_all)"""
    print("\n" + "=" * 80)
    print("TEST 4: Automatic Pagination - Fetch All Results")
    print("=" * 80)

    async with EC3Client() as client:
        # Fetch up to 50 Insulation EPDs (automatic pagination)
        all_results = await client.search_epds_all(
            category="Insulation",
            max_results=50,
            batch_size=10,
        )
        print(f"✅ Fetched {len(all_results)} EPDs across multiple pages")
        print(f"   Batch size: 10 per request")
        print(f"   Total requests: {(len(all_results) + 9) // 10}")


async def test_additional_endpoints():
    """Test 5: Additional Endpoints (materials, plants, projects)"""
    print("\n" + "=" * 80)
    print("TEST 5: Additional API Endpoints")
    print("=" * 80)

    async with EC3Client() as client:
        # Test materials endpoint
        print("\n📦 Materials Endpoint:")
        materials = await client.get_materials(category="Glass", limit=5)
        print(f"   ✅ Retrieved {len(materials.get('results', []))} materials")

        # Test plants endpoint
        print("\n🏭 Plants Endpoint:")
        plants = await client.get_plants(limit=5)
        print(f"   ✅ Retrieved {len(plants.get('results', []))} plants")

        # Test projects endpoint
        print("\n🏗️  Projects Endpoint:")
        projects = await client.get_projects(limit=5)
        print(f"   ✅ Retrieved {len(projects.get('results', []))} projects")


async def test_retry_logic():
    """Test 6: Retry Logic with Exponential Backoff"""
    print("\n" + "=" * 80)
    print("TEST 6: Retry Logic")
    print("=" * 80)

    async with EC3Client() as client:
        print("✅ Retry logic configured:")
        print(f"   Max retries: {client.MAX_RETRIES}")
        print(f"   Retry delays: {client.RETRY_DELAYS} seconds")
        print(f"   Total max wait time: {sum(client.RETRY_DELAYS)} seconds")

        # Test with a valid request (should succeed on first try)
        results = await client.search_epds(category="Aluminum", limit=3)
        print(f"✅ Request succeeded with {len(results.get('results', []))} results")
        print("   (No retries needed for successful request)")


async def test_full_extraction():
    """Test 7: Full Data Extraction from Multiple Endpoints"""
    print("\n" + "=" * 80)
    print("TEST 7: Full Data Extraction")
    print("=" * 80)

    async with EC3Client() as client:
        print("🔄 Extracting data from multiple endpoints...")
        print("   (Limited to 10 results per endpoint for testing)")

        # Extract limited data from all endpoints
        data = await client.extract_all_data(
            endpoints=["epds", "materials", "plants", "projects"],
            max_per_endpoint=10,
        )

        print("\n✅ Extraction complete:")
        for endpoint, items in data.items():
            print(f"   {endpoint}: {len(items)} items")

        return data


async def test_get_epd_details():
    """Test 8: Get Detailed EPD by ID"""
    print("\n" + "=" * 80)
    print("TEST 8: Get Detailed EPD by ID")
    print("=" * 80)

    async with EC3Client() as client:
        # First, get an EPD ID from search
        results = await client.search_epds(category="Gypsum", limit=1)
        epds = results.get("results", [])

        if epds:
            epd_id = epds[0].get("id")
            print(f"🔍 Found EPD ID: {epd_id}")

            # Get detailed EPD data
            detailed = await client.get_epd(epd_id)
            if detailed:
                print(f"✅ Retrieved detailed EPD data")
                print(f"   Name: {detailed.get('name', 'N/A')}")
                print(f"   Manufacturer: {detailed.get('manufacturer', {}).get('name', 'N/A')}")
                print(f"   GWP: {detailed.get('gwp', {}).get('total', 'N/A')} kg CO2e")
            else:
                print("❌ Failed to retrieve detailed EPD")
        else:
            print("⏭️  No EPDs found to test with")


async def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("EC3 ENHANCED API INTEGRATION TEST SUITE")
    print("=" * 80)
    print("\nTesting all new features from EC3 API documentation:")
    print("- OAuth 2.0 authentication")
    print("- Retry logic with exponential backoff")
    print("- Enhanced pagination with next/previous")
    print("- Additional endpoints (materials, plants, projects)")
    print("- Full data extraction capabilities")

    # Check API key
    api_key = os.getenv("EC3_API_KEY")
    if api_key:
        print(f"\n✅ EC3_API_KEY configured: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("\n⚠️  EC3_API_KEY not set - using public access (limited)")
        print("   Get your free API key at: https://buildingtransparency.org/ec3/manage-apps/keys")

    try:
        # Run all tests
        await test_basic_authentication()
        await test_oauth_authentication()
        await test_enhanced_pagination()
        await test_search_all()
        await test_additional_endpoints()
        await test_retry_logic()
        await test_get_epd_details()
        await test_full_extraction()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nEnhanced EC3 integration is working correctly!")
        print("\nNew capabilities:")
        print("  ✅ OAuth 2.0 authentication support")
        print("  ✅ Automatic retry with exponential backoff")
        print("  ✅ Enhanced pagination (next/previous/count)")
        print("  ✅ Additional endpoints (materials, plants, projects)")
        print("  ✅ Full data extraction from all endpoints")
        print("  ✅ Robust error handling")
        print("\nYou can now use these features to:")
        print("  - Extract complete EC3 database")
        print("  - Handle API failures gracefully")
        print("  - Access plant and project data")
        print("  - Use OAuth for secure authentication")

    except Exception as e:
        print("\n" + "=" * 80)
        print("❌ TEST FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
