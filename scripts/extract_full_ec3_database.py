#!/usr/bin/env python3
"""
Full EC3 Database Extraction Script

Based on EC3 API documentation for complete data extraction.
API Docs: https://buildingtransparency.org/ec3/manage-apps/api-doc/api

This script extracts from ALL EC3 API endpoints including:
- Core: EPDs (90,000+), Materials, Plants, Projects
- Users & Orgs: users, user_groups, orgs, plant_groups
- EPD Management: epd_requests, epd_imports, industry_epds, generic_estimates
- Standards: pcrs, baselines, reference_sets, categories, standards
- Projects: civil_projects, collections, buildings, BIM projects, elements
- Integrations: Procore, Autodesk Takeoff, Tally
- And more...

Uses the enhanced EC3Client with:
- Correct API base URL: https://buildingtransparency.org/api
- OAuth 2.0 authentication support
- Automatic pagination for all endpoints
- Retry logic with exponential backoff (2s, 4s, 8s, 16s)
- Comprehensive error handling (404, 401, rate limiting)
- Detailed progress tracking and statistics
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
    oauth_client_id = os.getenv("EC3_OAUTH_CLIENT_ID")
    oauth_client_secret = os.getenv("EC3_OAUTH_CLIENT_SECRET")
    api_key = os.getenv("EC3_API_KEY")

    if oauth_client_id and oauth_client_secret:
        print(f"\n✅ Using OAuth2 authentication")
        print(f"   Client ID: {oauth_client_id[:10]}...")
        auth_method = "OAuth2"
    elif api_key:
        print(f"\n✅ Using API key: {api_key[:10]}...{api_key[-4:]}")
        print("   Note: API keys may have limited endpoint access")
        auth_method = "API Key"
    else:
        print("\n❌ NO AUTHENTICATION CONFIGURED!")
        print("=" * 80)
        print("Most EC3 endpoints require authentication and will return 401 errors.")
        print()
        print("To set up authentication, run:")
        print("    python scripts/setup_ec3_credentials.py")
        print()
        print("Or manually configure credentials:")
        print("  • OAuth2 (recommended): https://buildingtransparency.org/ec3/manage-apps/")
        print("  • API Key (limited): https://buildingtransparency.org/ec3/manage-apps/keys")
        print("=" * 80)
        print()
        proceed = input("Continue anyway with no authentication? (yes/no): ").strip().lower()
        if proceed not in ["yes", "y"]:
            print("Extraction cancelled.")
            return
        auth_method = "None (Public Access Only)"

    # Initialize client
    async with EC3Client() as client:
        print("\n🔄 Validating credentials...")
        print("-" * 80)

        # Extract all data (with auth validation enabled by default)
        start_time = datetime.now()
        results = await client.extract_all_data(
            endpoints=endpoints,
            max_per_endpoint=max_per_endpoint,
            validate_auth=True,
            stop_on_auth_failure=True,
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Check auth validation results
        auth_validation = results.get("auth_validation")
        if auth_validation:
            print(f"\nAuthentication Validation:")
            print(f"   Method: {auth_validation['auth_method']}")
            print(f"   Status: {'✅ VALID' if auth_validation['valid'] else '❌ INVALID'}")
            print(f"   Message: {auth_validation['message']}")

            if not auth_validation["valid"]:
                print("\n" + "=" * 80)
                print("❌ AUTHENTICATION FAILED")
                print("=" * 80)
                print()
                print("Your credentials are invalid or expired.")
                print("Please run: python scripts/setup_ec3_credentials.py")
                print()
                return

        # Check if extraction stopped early
        if results["summary"].get("stopped_early"):
            print(f"\n⚠️  Extraction stopped early: {results['summary'].get('stop_reason')}")
            return

        print("\n🔄 Extraction starting...")
        print("-" * 80)

        # Extract data and stats from new return format
        data = results.get("data", {})
        stats = results.get("stats", {})
        summary = results.get("summary", {})

        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE")
        print("=" * 80)

        # Display results by endpoint
        successful_endpoints = []
        failed_endpoints = []

        for endpoint in stats.keys():
            endpoint_stats = stats[endpoint]
            status = endpoint_stats.get("status", "unknown")
            count = endpoint_stats.get("count", 0)

            if status == "success" and count > 0:
                successful_endpoints.append((endpoint, count))
            else:
                error = endpoint_stats.get("error", "unknown")
                failed_endpoints.append((endpoint, status, error))

        # Save successful endpoints to JSON files
        for endpoint, count in successful_endpoints:
            items = data.get(endpoint, [])

            # Save to file
            output_file = output_path / f"{endpoint}.json"
            with open(output_file, "w") as f:
                json.dump(items, f, indent=2)

            print(f"\n✅ {endpoint}:")
            print(f"   Status: SUCCESS")
            print(f"   Records: {count:,}")
            print(f"   File: {output_file}")
            print(f"   Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")

        # Display failed endpoints
        if failed_endpoints:
            print("\n" + "-" * 80)
            print("FAILED/EMPTY ENDPOINTS:")
            print("-" * 80)
            for endpoint, status, error in failed_endpoints:
                print(f"\n❌ {endpoint}:")
                print(f"   Status: {status.upper()}")
                print(f"   Error: {error}")
                if error == "not_found":
                    print(f"   Note: Endpoint may not exist or requires authentication")
                elif error == "unauthorized":
                    print(f"   Note: Authentication required - set EC3_API_KEY")

        # Save metadata
        metadata = {
            "extraction_date": datetime.now().isoformat(),
            "authentication_method": auth_method,
            "duration_seconds": duration,
            "api_base_url": "https://buildingtransparency.org/api",
            "endpoints_attempted": list(stats.keys()),
            "endpoints_successful": [e for e, _ in successful_endpoints],
            "endpoints_failed": [e for e, _, _ in failed_endpoints],
            "summary": summary,
            "stats_by_endpoint": stats,
        }

        metadata_file = output_path / "metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total endpoints attempted: {summary.get('total_endpoints', 0)}")
        print(f"Successful: {summary.get('successful', 0)}")
        print(f"Failed: {summary.get('failed', 0)}")
        print(f"  - Not found (404): {summary.get('not_found', 0)}")
        print(f"  - Unauthorized (401): {summary.get('unauthorized', 0)}")
        print(f"Total records extracted: {summary.get('total_records', 0):,}")
        print(f"Total time: {duration:.1f} seconds")
        if summary.get('total_records', 0) > 0 and duration > 0:
            print(f"Average rate: {summary.get('total_records', 0) / duration:.1f} records/second")
        print(f"\nAll data saved to: {output_path.absolute()}")
        print(f"Metadata saved to: {metadata_file}")

        return results


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
        choices=[
            "epds", "materials", "plants", "projects",
            "users", "user_groups", "orgs", "plant_groups",
            "epd_requests", "epd_imports", "industry_epds", "generic_estimates",
            "pcrs", "baselines", "reference_sets", "categories", "standards",
            "civil_projects", "collections", "building_groups", "building_campuses",
            "building_complexes", "project_views", "bim_projects", "elements",
            "procore", "autodesk_takeoff", "bid_leveling_sheets", "tally_projects",
            "charts", "dashboard", "docs", "access_management", "configurations", "jobs"
        ],
        help="Specific endpoints to extract (default: all available endpoints)",
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
