#!/usr/bin/env python3
"""
EC3 API Diagnostic Tool

Tests EC3 API endpoints and shows actual responses to diagnose import issues.
"""

import asyncio
import json
import os

import aiohttp

from mothra.config import settings


async def test_ec3_endpoints():
    """Test various EC3 API endpoints to understand response format."""
    api_key = settings.ec3_api_key or os.getenv("EC3_API_KEY")

    if not api_key:
        print("❌ No EC3 API key found!")
        print("   Set EC3_API_KEY in .env file")
        return

    print("=" * 80)
    print("EC3 API DIAGNOSTIC TOOL")
    print("=" * 80)
    print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
    print()

    headers = {"Authorization": f"Bearer {api_key}"}

    async with aiohttp.ClientSession(
        headers=headers, timeout=aiohttp.ClientTimeout(total=60)
    ) as session:
        # ========================================
        # Test 1: List EPDs (no filters)
        # ========================================
        print("📦 TEST 1: List EPDs (no filters, limit=5)")
        print("-" * 80)

        url = "https://openepd.buildingtransparency.org/api/epds"
        params = {"limit": 5}

        try:
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('Content-Type')}")

                if response.status == 200:
                    data = await response.json()
                    print(f"Response Type: {type(data)}")

                    if isinstance(data, dict):
                        print(f"Dict Keys: {list(data.keys())}")
                        if "results" in data:
                            print(f"Results Count: {len(data.get('results', []))}")
                            print(f"Total Count: {data.get('count', 'N/A')}")
                        print(f"\nFirst 500 chars of response:")
                        print(json.dumps(data, indent=2)[:500])
                    elif isinstance(data, list):
                        print(f"List Length: {len(data)}")
                        print(f"\nFirst item:")
                        if data:
                            print(json.dumps(data[0], indent=2)[:500])
                    else:
                        print(f"Unexpected type: {type(data)}")

                else:
                    error_text = await response.text()
                    print(f"Error: {error_text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

        print("\n")

        # ========================================
        # Test 2: Search with category parameter
        # ========================================
        print("📦 TEST 2: Search with category='Concrete'")
        print("-" * 80)

        params = {"category": "Concrete", "limit": 5}

        try:
            async with session.get(url, params=params) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print(f"Response Type: {type(data)}")

                    if isinstance(data, dict):
                        print(f"Dict Keys: {list(data.keys())}")
                        results_count = len(data.get("results", []))
                        print(f"Results Count: {results_count}")
                    elif isinstance(data, list):
                        print(f"List Length: {len(data)}")
                    else:
                        print(f"Unexpected type: {type(data)}")

                    print(f"\nFirst 300 chars of response:")
                    print(json.dumps(data, indent=2)[:300])

                else:
                    error_text = await response.text()
                    print(f"Error: {error_text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

        print("\n")

        # ========================================
        # Test 3: Try different category values
        # ========================================
        print("📦 TEST 3: Try different category values")
        print("-" * 80)

        test_categories = [
            "concrete",  # lowercase
            "Concrete",  # capitalized
            "CONCRETE",  # uppercase
        ]

        for cat in test_categories:
            params = {"category": cat, "limit": 1}

            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            count = len(data.get("results", []))
                        elif isinstance(data, list):
                            count = len(data)
                        else:
                            count = 0

                        print(f"category='{cat}': {count} results")
                    else:
                        print(f"category='{cat}': HTTP {response.status}")

            except Exception as e:
                print(f"category='{cat}': Error - {e}")

        print("\n")

        # ========================================
        # Test 4: Try query parameter instead
        # ========================================
        print("📦 TEST 4: Try query (q) parameter")
        print("-" * 80)

        test_queries = [
            ("Concrete", 'q="Concrete"'),
            ("concrete", 'q="concrete"'),
            ("", "q=Concrete (no quotes)"),
        ]

        for query_val, desc in test_queries:
            if query_val:
                params = {"q": query_val, "limit": 1}
            else:
                params = {"q": "Concrete", "limit": 1}

            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            count = len(data.get("results", []))
                        elif isinstance(data, list):
                            count = len(data)
                        else:
                            count = 0

                        print(f"{desc}: {count} results")
                    else:
                        print(f"{desc}: HTTP {response.status}")

            except Exception as e:
                print(f"{desc}: Error - {e}")

        print("\n")

        # ========================================
        # Test 5: Check for pagination info
        # ========================================
        print("📦 TEST 5: Check pagination with offset")
        print("-" * 80)

        params = {"limit": 2, "offset": 0}

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"Response Type: {type(data)}")

                    if isinstance(data, dict):
                        print(f"Dict Keys: {list(data.keys())}")
                        print(f"\nFull response structure:")
                        # Show full structure without data
                        structure = {k: type(v).__name__ for k, v in data.items()}
                        print(json.dumps(structure, indent=2))

                        if "next" in data:
                            print(f"\nNext URL: {data['next']}")
                        if "previous" in data:
                            print(f"Previous URL: {data['previous']}")
                        if "count" in data:
                            print(f"Total Count: {data['count']}")

        except Exception as e:
            print(f"❌ Exception: {e}")

        print("\n")

        # ========================================
        # Test 6: Try materials endpoint
        # ========================================
        print("📦 TEST 6: Try /materials endpoint")
        print("-" * 80)

        materials_url = "https://openepd.buildingtransparency.org/api/materials"
        params = {"limit": 5}

        try:
            async with session.get(materials_url, params=params) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    print(f"Response Type: {type(data)}")

                    if isinstance(data, dict):
                        print(f"Dict Keys: {list(data.keys())}")
                        if "results" in data:
                            print(f"Results Count: {len(data.get('results', []))}")
                    elif isinstance(data, list):
                        print(f"List Length: {len(data)}")

                    print(f"\nFirst 300 chars:")
                    print(json.dumps(data, indent=2)[:300])

                else:
                    error_text = await response.text()
                    print(f"Error: {error_text[:200]}")

        except Exception as e:
            print(f"❌ Exception: {e}")

        print("\n")

    print("=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("Based on the responses above:")
    print("1. Check what parameter names work (category, q, etc.)")
    print("2. Check response structure (dict with 'results' vs list)")
    print("3. Check if 0 results means wrong parameters or empty dataset")
    print("4. Verify API key has proper permissions")
    print()


async def main():
    """Run diagnostic tests."""
    await test_ec3_endpoints()


if __name__ == "__main__":
    asyncio.run(main())
