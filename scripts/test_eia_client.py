#!/usr/bin/env python3
"""
Test script for EIA API client.

This script verifies that the EIA client can connect to the API and fetch data.
Run this before attempting full ingestion to verify your API key works.

Usage:
    python scripts/test_eia_client.py
    python scripts/test_eia_client.py --api-key YOUR_KEY
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mothra.agents.discovery.eia_integration import EIAClient


async def test_client(api_key: str | None = None):
    """Test EIA client functionality."""
    print("=" * 60)
    print("EIA API Client Test")
    print("=" * 60)

    try:
        async with EIAClient(api_key=api_key) as client:
            print(f"\n✓ Client initialized successfully")
            print(f"  Base URL: {client.base_url}")
            print(f"  API Key: {'Set' if client.api_key else 'Not Set (will use public access)'}")

            # Test 1: Fetch small facility dataset
            print("\n[Test 1] Fetching facility fuel data (CA, 5 records)...")
            try:
                facilities = await client.get_facility_fuel_data(
                    state_ids=["CA"],
                    frequency="annual",
                    max_records=5,
                )
                print(f"✓ Success! Fetched {len(facilities)} facility records")
                if facilities:
                    sample = facilities[0]
                    print(f"  Sample record keys: {list(sample.keys())[:8]}...")
                    print(f"  Sample plant: {sample.get('plantName', 'N/A')}")
            except Exception as e:
                print(f"✗ Failed: {e}")
                return False

            # Test 2: Fetch CO2 emissions
            print("\n[Test 2] Fetching CO2 emissions aggregates (CA, 5 records)...")
            try:
                emissions = await client.get_co2_emissions_aggregates(
                    state_ids=["CA"],
                    max_records=5,
                )
                print(f"✓ Success! Fetched {len(emissions)} emission records")
                if emissions:
                    sample = emissions[0]
                    print(f"  Sample record keys: {list(sample.keys())[:8]}...")
                    state = sample.get("stateId") or sample.get("stateid", "N/A")
                    print(f"  Sample state: {state}")
            except Exception as e:
                print(f"✗ Failed: {e}")
                return False

            # Test 3: Generic endpoint test
            print("\n[Test 3] Testing generic endpoint access...")
            try:
                response = await client.get_endpoint(
                    route="electricity/facility-fuel",
                    facets={"state": ["TX"]},
                    frequency="annual",
                    length=3,
                )
                if response:
                    data = response.get("response", {}).get("data", [])
                    print(f"✓ Success! Generic endpoint returned {len(data)} records")
                else:
                    print(f"✗ No response from endpoint")
                    return False
            except Exception as e:
                print(f"✗ Failed: {e}")
                return False

            print("\n" + "=" * 60)
            print("✓ ALL TESTS PASSED!")
            print("=" * 60)
            print("\nYour EIA API client is working correctly.")
            print("You can now run the full ingestion script:")
            print("  python scripts/ingest_eia_data.py --all --max-records 100")
            print("\nTo ingest all data:")
            print("  python scripts/ingest_eia_data.py --all")
            return True

    except Exception as e:
        print(f"\n✗ Client initialization failed: {e}")
        print("\nTroubleshooting:")
        print("1. Verify your EIA_API_KEY is set in .env file")
        print("2. Get a free API key from: https://www.eia.gov/opendata/")
        print("3. Check your internet connection")
        return False


def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="Test EIA API client connectivity and functionality"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="EIA API key (or set EIA_API_KEY environment variable)",
    )

    args = parser.parse_args()

    # Run test
    success = asyncio.run(test_client(api_key=args.api_key))

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
