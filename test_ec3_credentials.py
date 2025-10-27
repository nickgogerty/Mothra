#!/usr/bin/env python3
"""
Quick test script to validate EC3 credentials using MOTHRA's EC3Client.

This script will:
1. Load credentials from .env
2. Test OAuth2 (if configured)
3. Test API key (if configured)
4. Report which authentication method works
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from mothra.agents.discovery.ec3_integration import EC3Client


async def test_credentials():
    """Test EC3 credentials and report results."""
    print("=" * 80)
    print("EC3 CREDENTIALS VALIDATION TEST")
    print("=" * 80)

    async with EC3Client() as client:
        # Validate credentials
        result = await client.validate_credentials()

        print(f"\nAuthentication Method: {result['auth_method']}")
        print(f"Valid: {result['valid']}")
        print(f"Message: {result['message']}")

        if result.get('test_result'):
            print(f"\nTest Endpoint: {result['test_endpoint']}")
            print(f"Results Count: {result['test_result'].get('results_count', 0)}")
            print(f"Total Count: {result['test_result'].get('count', 0)}")

        print("\n" + "=" * 80)

        if result['valid']:
            print("✓ SUCCESS: Credentials are valid!")
            print(f"✓ Using: {result['auth_method']}")

            # Try to fetch some EPDs
            print("\nTesting EPD search...")
            epds = await client.search_epds(query="concrete", limit=5)

            if epds and epds.get('results'):
                print(f"✓ Found {len(epds['results'])} concrete EPDs")
                print(f"✓ Total available: {epds.get('count', 'unknown')}")

                print("\nSample EPDs:")
                for i, epd in enumerate(epds['results'][:3], 1):
                    name = epd.get('name', 'Unknown')
                    print(f"  {i}. {name[:70]}")

                print("\n✓ EC3 integration is working correctly!")
            else:
                print("⚠ Search returned no results (may be authentication issue)")

        else:
            print("✗ FAILED: Credentials are not valid")
            print(f"\nError: {result['message']}")
            print("\n📋 Next Steps:")
            print("1. Check EC3_AUTHENTICATION_GUIDE.md for detailed troubleshooting")
            print("2. Verify OAuth2 application exists at:")
            print("   https://buildingtransparency.org/ec3/manage-apps")
            print("3. Or get an API key from:")
            print("   https://buildingtransparency.org/ec3/manage-apps/keys")

        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_credentials())
