#!/usr/bin/env python3
"""
Full EC3 Database Extraction Script

Based on EC3 API documentation guide for complete data extraction.

This script demonstrates how to extract the entire EC3 database:
- EPDs (90,000+)
- Materials
- Manufacturing Plants
- Projects

Uses the enhanced EC3Client with:
- OAuth 2.0 authentication
- Automatic pagination
- Retry logic with exponential backoff
- Progress tracking
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mothra.agents.discovery.ec3_integration import EC3Client


async def extract_full_database(
    output_dir: str = "ec3_data_export",
    endpoints: list[str] = None,
    max_per_endpoint: int = None,
):
    """
    Extract full EC3 database to JSON files.

    Args:
        output_dir: Directory to save exported data
        endpoints: List of endpoints to extract (default: all)
        max_per_endpoint: Maximum results per endpoint (None = unlimited)
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print("=" * 80)
    print("EC3 FULL DATABASE EXTRACTION")
    print("=" * 80)
    print(f"\nOutput directory: {output_path.absolute()}")
    print(f"Endpoints: {endpoints or 'all (epds, materials, plants, projects)'}")
    print(f"Max per endpoint: {max_per_endpoint or 'unlimited'}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Check authentication
    api_key = os.getenv("EC3_API_KEY")
    if api_key:
        print(f"\n✅ Using API key: {api_key[:10]}...{api_key[-4:]}")
        auth_method = "API Key"
    else:
        print("\n⚠️  No API key configured - using public access")
        print("   Note: Public access may have rate limits")
        print("   Get a free API key: https://buildingtransparency.org/ec3/manage-apps/keys")
        auth_method = "Public"

    # Initialize client
    async with EC3Client() as client:
        print("\n🔄 Extraction starting...")
        print("-" * 80)

        # Extract all data
        start_time = datetime.now()
        data = await client.extract_all_data(
            endpoints=endpoints,
            max_per_endpoint=max_per_endpoint,
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE")
        print("=" * 80)

        # Save to JSON files
        total_records = 0
        for endpoint, items in data.items():
            count = len(items)
            total_records += count

            # Save to file
            output_file = output_path / f"{endpoint}.json"
            with open(output_file, "w") as f:
                json.dump(items, f, indent=2)

            print(f"\n✅ {endpoint}:")
            print(f"   Records: {count:,}")
            print(f"   File: {output_file}")
            print(f"   Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

        # Save metadata
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "authentication_method": auth_method,
            "duration_seconds": duration,
            "endpoints": list(data.keys()),
            "total_records": total_records,
            "record_counts": {k: len(v) for k, v in data.items()},
        }

        metadata_file = output_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total records: {total_records:,}")
        print(f"Total time: {duration:.1f} seconds")
        print(f"Average rate: {total_records / duration:.1f} records/second")
        print(f"\nAll data saved to: {output_path.absolute()}")
        print(f"Metadata saved to: {metadata_file}")

        return data


async def extract_by_category(
    categories: list[str] = None,
    output_dir: str = "ec3_data_by_category",
    max_per_category: int = None,
):
    """
    Extract EPDs by material category.

    Args:
        categories: List of categories (default: common construction materials)
        output_dir: Directory to save exported data
        max_per_category: Maximum EPDs per category
    """
    if categories is None:
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

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print("=" * 80)
    print("EC3 CATEGORY-BASED EXTRACTION")
    print("=" * 80)
    print(f"\nOutput directory: {output_path.absolute()}")
    print(f"Categories: {', '.join(categories)}")
    print(f"Max per category: {max_per_category or 'unlimited'}")

    async with EC3Client() as client:
        results = {}

        for category in categories:
            print(f"\n🔄 Extracting {category}...")

            # Extract all EPDs for this category
            epds = await client.search_epds_all(
                category=category,
                max_results=max_per_category,
                batch_size=1000,
            )

            results[category] = epds

            # Save to file
            output_file = output_path / f"{category.lower()}.json"
            with open(output_file, "w") as f:
                json.dump(epds, f, indent=2)

            print(f"   ✅ {len(epds):,} EPDs saved to {output_file}")

        print("\n" + "=" * 80)
        print("CATEGORY EXTRACTION COMPLETE")
        print("=" * 80)

        for category, epds in results.items():
            print(f"{category:15s}: {len(epds):6,} EPDs")

        total = sum(len(epds) for epds in results.values())
        print(f"{'TOTAL':15s}: {total:6,} EPDs")

        return results


def main():
    """Main function with CLI options"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract EC3 database to JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Extract all endpoints (limited to 100 per endpoint for testing)
  python scripts/extract_full_ec3_database.py --test

  # Extract specific endpoints
  python scripts/extract_full_ec3_database.py --endpoints epds materials

  # Extract by category
  python scripts/extract_full_ec3_database.py --by-category

  # Extract unlimited (full database - will take time!)
  python scripts/extract_full_ec3_database.py --full

  # Extract specific categories with limit
  python scripts/extract_full_ec3_database.py --by-category --categories Concrete Steel Wood --limit 1000

""",
    )

    parser.add_argument(
        "--output-dir",
        default="ec3_data_export",
        help="Output directory (default: ec3_data_export)",
    )

    parser.add_argument(
        "--endpoints",
        nargs="+",
        choices=["epds", "materials", "plants", "projects"],
        help="Specific endpoints to extract (default: all)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum results per endpoint (default: unlimited)",
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode: Extract only 100 records per endpoint",
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help="Full extraction mode: Extract all available data (no limits)",
    )

    parser.add_argument(
        "--by-category",
        action="store_true",
        help="Extract EPDs by material category instead of by endpoint",
    )

    parser.add_argument(
        "--categories",
        nargs="+",
        help="Specific categories to extract (only with --by-category)",
    )

    args = parser.parse_args()

    # Determine limit
    if args.test:
        limit = 100
        print("\n🧪 TEST MODE: Limiting to 100 records per endpoint\n")
    elif args.full:
        limit = None
        print("\n⚠️  FULL EXTRACTION MODE: This will take significant time!\n")
    else:
        limit = args.limit

    # Run extraction
    if args.by_category:
        asyncio.run(
            extract_by_category(
                categories=args.categories,
                output_dir=args.output_dir,
                max_per_category=limit,
            )
        )
    else:
        asyncio.run(
            extract_full_database(
                output_dir=args.output_dir,
                endpoints=args.endpoints,
                max_per_endpoint=limit,
            )
        )


if __name__ == "__main__":
    main()
