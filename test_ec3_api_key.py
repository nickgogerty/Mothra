#!/usr/bin/env python3
"""
Comprehensive EC3 API Key Testing Script.

Tests the API key with multiple authentication methods and endpoints
to determine if API key authentication can work as an alternative to OAuth2.
"""

import asyncio
import os
from dotenv import load_dotenv
import aiohttp
import json

# Load .env
load_dotenv()


async def test_api_key_comprehensive():
    """Test EC3 API key with multiple configurations."""
    print("=" * 80)
    print("EC3 API KEY COMPREHENSIVE TEST")
    print("=" * 80)

    api_key = os.getenv("EC3_API_KEY")

    if not api_key:
        print("\n❌ No API key found in .env file (EC3_API_KEY)")
        return

    print(f"\nAPI Key: {api_key[:20]}... (length: {len(api_key)})")

    # List of endpoints to test
    endpoints = [
        {"path": "epds", "name": "EPDs (main data)"},
        {"path": "materials", "name": "Materials"},
        {"path": "plants", "name": "Manufacturing plants"},
        {"path": "orgs", "name": "Organizations"},
        {"path": "categories", "name": "Categories"},
        {"path": "pcrs", "name": "Product Category Rules"},
    ]

    # Authentication methods to try
    auth_methods = [
        {
            "name": "Bearer token (standard)",
            "headers": {"Authorization": f"Bearer {api_key}"}
        },
        {
            "name": "API key header",
            "headers": {"X-API-Key": api_key}
        },
        {
            "name": "Token header",
            "headers": {"Token": api_key}
        },
    ]

    print("\n" + "=" * 80)
    print("TESTING API KEY WITH DIFFERENT AUTHENTICATION METHODS")
    print("=" * 80)

    successful_methods = []

    for auth_method in auth_methods:
        print(f"\n{'─' * 80}")
        print(f"▶ Testing: {auth_method['name']}")
        print(f"{'─' * 80}")

        success_count = 0

        for endpoint in endpoints:
            url = f"https://buildingtransparency.org/api/{endpoint['path']}"

            try:
                async with aiohttp.ClientSession() as session:
                    headers = auth_method['headers'].copy()
                    headers["Accept"] = "application/json"

                    async with session.get(
                        url,
                        headers=headers,
                        params={"limit": 1},
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        status = response.status

                        if status == 200:
                            success_count += 1
                            data = await response.json()

                            # Extract count
                            if isinstance(data, dict):
                                count = data.get("count", len(data.get("results", [])))
                            elif isinstance(data, list):
                                count = len(data)
                            else:
                                count = "unknown"

                            print(f"  ✓ {endpoint['name']:<30} Status: 200  Count: {count}")
                        elif status == 401:
                            error = await response.text()
                            print(f"  ✗ {endpoint['name']:<30} Status: 401  (Unauthorized)")
                        elif status == 404:
                            print(f"  ⚠ {endpoint['name']:<30} Status: 404  (Not Found/Private)")
                        else:
                            print(f"  ⚠ {endpoint['name']:<30} Status: {status}")

            except Exception as e:
                print(f"  ✗ {endpoint['name']:<30} Error: {str(e)[:50]}")

        if success_count > 0:
            successful_methods.append({
                "method": auth_method['name'],
                "success_count": success_count,
                "total": len(endpoints)
            })
            print(f"\n  ✓ SUCCESS: {success_count}/{len(endpoints)} endpoints accessible")
        else:
            print(f"\n  ✗ FAILED: 0/{len(endpoints)} endpoints accessible")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if successful_methods:
        print("\n✓ API KEY WORKS! The following authentication methods succeeded:\n")
        for method in successful_methods:
            print(f"  • {method['method']}: {method['success_count']}/{method['total']} endpoints")

        print("\n💡 RECOMMENDATION:")
        print("   Use the API key for authentication instead of OAuth2.")
        print("   The EC3Client already supports API key authentication.")
        print("")
        print("   Update your .env to use API key only:")
        print("   1. Keep: EC3_API_KEY=JAWnY2CsrYkXcX4m7xQGb7zbmMstPx")
        print("   2. Comment out or remove OAuth2 credentials:")
        print("      # EC3_OAUTH_CLIENT_ID=...")
        print("      # EC3_OAUTH_CLIENT_SECRET=...")
        print("      # EC3_OAUTH_USERNAME=...")
        print("      # EC3_OAUTH_PASSWORD=...")

    else:
        print("\n❌ API KEY DOES NOT WORK")
        print("\nNone of the authentication methods succeeded.")
        print("\nPossible issues:")
        print("1. The API key is invalid or expired")
        print("2. The API key doesn't have proper permissions")
        print("3. The EC3 API requires OAuth2 for all endpoints")

        print("\n📋 NEXT STEPS FOR OAUTH2:")
        print("\n1. Log into EC3:")
        print("   https://buildingtransparency.org/")
        print("")
        print("2. Go to OAuth Applications:")
        print("   https://buildingtransparency.org/ec3/manage-apps")
        print("")
        print("3. Check if 'mothratest' application exists:")
        print("   - If it doesn't exist, create a new OAuth application")
        print("   - Enable 'Password Grant' flow")
        print("   - Copy the new Client ID and Client Secret")
        print("")
        print("4. Update .env with new credentials:")
        print("   EC3_OAUTH_CLIENT_ID=<new_client_id>")
        print("   EC3_OAUTH_CLIENT_SECRET=<new_client_secret>")
        print("")
        print("5. Or try getting a new API key:")
        print("   https://buildingtransparency.org/ec3/manage-apps/keys")


async def test_public_access():
    """Test if public access (no authentication) works."""
    print("\n" + "=" * 80)
    print("PUBLIC ACCESS TEST (No Authentication)")
    print("=" * 80)

    url = "https://buildingtransparency.org/api/epds"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                params={"limit": 5},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                status = response.status

                if status == 200:
                    data = await response.json()
                    if isinstance(data, dict):
                        count = data.get("count", "unknown")
                        results = len(data.get("results", []))
                    elif isinstance(data, list):
                        count = len(data)
                        results = len(data)
                    else:
                        count = "unknown"
                        results = 0

                    print(f"\n✓ Public access WORKS!")
                    print(f"  Total EPDs: {count}")
                    print(f"  Results returned: {results}")
                    print("\n  Sample EPD names:")

                    results_list = data.get("results", []) if isinstance(data, dict) else data
                    for i, epd in enumerate(results_list[:3], 1):
                        name = epd.get("name", "Unknown")
                        print(f"    {i}. {name[:60]}")

                    print("\n💡 Public access is available but may be rate-limited.")

                elif status == 401:
                    print("\n✗ Public access requires authentication (401)")
                else:
                    error = await response.text()
                    print(f"\n⚠ Public access returned status {status}")
                    print(f"  Response: {error[:200]}")

    except Exception as e:
        print(f"\n✗ Public access test failed: {e}")


async def main():
    """Run all diagnostic tests."""
    await test_api_key_comprehensive()
    await test_public_access()

    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
