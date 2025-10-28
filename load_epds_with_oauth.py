#!/usr/bin/env python3
"""
EPD Loader with Explicit OAuth Configuration
=============================================
This version explicitly loads and passes OAuth credentials to EC3Client
to avoid any Settings initialization issues.

Usage:
    python load_epds_with_oauth.py [--limit N]
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime, UTC

# Load .env FIRST, before any imports
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✓ Loaded .env from: {env_path}")
else:
    print(f"⚠️  .env not found at: {env_path}")
    sys.exit(1)

# Now verify OAuth credentials are loaded
print("\nVerifying OAuth credentials from environment:")
oauth_client_id = os.getenv('EC3_OAUTH_CLIENT_ID')
oauth_client_secret = os.getenv('EC3_OAUTH_CLIENT_SECRET')
oauth_username = os.getenv('EC3_OAUTH_USERNAME')
oauth_password = os.getenv('EC3_OAUTH_PASSWORD')
oauth_scope = os.getenv('EC3_OAUTH_SCOPE', 'read')
api_key = os.getenv('EC3_API_KEY')

print(f"  EC3_API_KEY: {'✓ ' + api_key[:15] + '...' if api_key else '❌ NOT SET'}")
print(f"  EC3_OAUTH_CLIENT_ID: {'✓ ' + oauth_client_id[:15] + '...' if oauth_client_id else '❌ NOT SET'}")
print(f"  EC3_OAUTH_CLIENT_SECRET: {'✓ SET' if oauth_client_secret else '❌ NOT SET'}")
print(f"  EC3_OAUTH_USERNAME: {'✓ ' + oauth_username if oauth_username else '❌ NOT SET'}")
print(f"  EC3_OAUTH_PASSWORD: {'✓ SET' if oauth_password else '❌ NOT SET'}")
print(f"  EC3_OAUTH_SCOPE: {oauth_scope}")

# Check if we have OAuth credentials
has_oauth = all([oauth_client_id, oauth_client_secret, oauth_username, oauth_password])
has_api_key = bool(api_key)

if not has_oauth and not has_api_key:
    print("\n❌ ERROR: No credentials found!")
    print("Please check your .env file and ensure OAuth or API key credentials are set.")
    sys.exit(1)

if not has_oauth:
    print("\n⚠️  WARNING: OAuth credentials incomplete. Will use API key only.")
    print("Some endpoints may not be accessible with just an API key.")
    oauth_config = None
else:
    print("\n✓ OAuth credentials loaded successfully!")
    oauth_config = {
        'grant_type': 'password',
        'client_id': oauth_client_id,
        'client_secret': oauth_client_secret,
        'username': oauth_username,
        'password': oauth_password,
        'scope': oauth_scope,
    }

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Now import mothra modules
from mothra.agents.discovery.ec3_integration import EC3Client, EC3EPDParser
from mothra.db.session import AsyncSessionLocal
from mothra.db.models import CarbonEntity, DataSource
from mothra.db.models_verification import CarbonEntityVerification
from sqlalchemy import select


async def load_epds(limit: int = None):
    """Load EPDs from EC3 with explicit OAuth config."""

    print("\n" + "=" * 70)
    print("EPD LOADER WITH EXPLICIT OAUTH")
    print("=" * 70)
    print(f"Limit: {limit or 'All EPDs'}")
    print(f"Auth method: {'OAuth2 + API key fallback' if oauth_config else 'API key only'}")
    print("=" * 70)

    # Create EC3 client with explicit config
    ec3_client = EC3Client(
        api_key=api_key,
        oauth_config=oauth_config,
        auto_load_credentials=False  # We loaded them manually
    )

    stats = {
        'fetched': 0,
        'processed': 0,
        'errors': 0,
        'start_time': datetime.now(UTC)
    }

    try:
        # Get or create data source
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(DataSource).where(DataSource.name == "EC3 (Building Transparency)")
            )
            data_source = result.scalar_one_or_none()

            if not data_source:
                data_source = DataSource(
                    name="EC3 (Building Transparency)",
                    url="https://buildingtransparency.org",
                    source_type="api",
                    category="epd_database",
                    access_method="rest_api",
                    auth_required=True,
                    update_frequency="daily",
                    status="active"
                )
                session.add(data_source)
                await session.commit()
                await session.refresh(data_source)
                print(f"✓ Created data source: {data_source.name}")

        # Test credentials first
        print("\nTesting EC3 API credentials...")
        async with ec3_client as client:
            validation = await client.validate_credentials()

            if not validation['valid']:
                print(f"\n❌ Credential validation failed!")
                print(f"   Auth method: {validation['auth_method']}")
                print(f"   Message: {validation['message']}")
                return stats

            print(f"✓ Credentials valid ({validation['auth_method']})")

            # Fetch EPDs
            print(f"\nFetching EPDs...")
            offset = 0
            batch_size = 100
            parser = EC3EPDParser()

            while True:
                print(f"\n--- Batch at offset {offset} ---")

                response = await client.search_epds(limit=batch_size, offset=offset)

                if not response or 'results' not in response:
                    print("No response or results")
                    break

                epds = response['results']
                if not epds:
                    print("✓ No more EPDs")
                    break

                stats['fetched'] += len(epds)
                print(f"✓ Fetched {len(epds)} EPDs (total: {stats['fetched']})")

                # Process EPDs
                async with AsyncSessionLocal() as session:
                    for i, epd_data in enumerate(epds, 1):
                        try:
                            # Parse EPD
                            entity_data, verification_data = parser.parse_epd_to_entity(
                                epd_data, data_source
                            )

                            # Create entity
                            entity = CarbonEntity(
                                source_id=data_source.id,
                                entity_type='product',
                                name=entity_data.get('name'),
                                description=entity_data.get('description'),
                                category_hierarchy=entity_data.get('category_hierarchy', []),
                                geographic_scope=entity_data.get('geographic_scope'),
                                quality_score=entity_data.get('quality_score', 0.7),
                                confidence_level='medium',
                                validation_status='pending',
                                raw_data=epd_data,
                                extra_metadata=entity_data.get('extra_metadata', {})
                            )
                            session.add(entity)
                            await session.flush()

                            # Create verification
                            if verification_data:
                                verification = CarbonEntityVerification(
                                    entity_id=entity.id,
                                    epd_registration_number=verification_data.get('epd_registration_number'),
                                    openepd_id=verification_data.get('openepd_id'),
                                    verification_status=verification_data.get('verification_status', 'pending'),
                                    gwp_total=verification_data.get('gwp_total'),
                                    lca_stages_included=verification_data.get('lca_stages_included', []),
                                    extra_metadata=verification_data.get('verification_metadata', {})
                                )
                                session.add(verification)

                            stats['processed'] += 1

                            if stats['processed'] % 10 == 0:
                                await session.commit()
                                print(f"  Processed {stats['processed']}/{stats['fetched']} EPDs...")

                        except Exception as e:
                            stats['errors'] += 1
                            print(f"  ✗ Error processing EPD: {e}")
                            continue

                    await session.commit()
                    print(f"✓ Batch committed ({stats['processed']} total)")

                # Check limit
                if limit and stats['fetched'] >= limit:
                    print(f"✓ Reached limit of {limit}")
                    break

                # Check for more pages
                if not response.get('next'):
                    print("✓ No more pages")
                    break

                offset += batch_size
                await asyncio.sleep(0.1)  # Rate limiting

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Print summary
        elapsed = (datetime.now(UTC) - stats['start_time']).total_seconds()
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Fetched:    {stats['fetched']}")
        print(f"Processed:  {stats['processed']}")
        print(f"Errors:     {stats['errors']}")
        print(f"Time:       {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
        if stats['processed'] > 0:
            print(f"Rate:       {stats['processed']/elapsed:.2f} EPDs/sec")
        print("=" * 70)

    return stats


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Load EPDs with explicit OAuth config')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of EPDs')
    args = parser.parse_args()

    await load_epds(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
