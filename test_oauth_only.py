#!/usr/bin/env python3
"""
Test OAuth2 Authentication Only
================================
This script tests ONLY OAuth2 authentication with EC3 API.

Usage:
    python test_oauth_only.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Load .env FIRST
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"✓ Loaded .env from: {env_path}")
else:
    print(f"❌ .env not found at: {env_path}")
    sys.exit(1)

print("\n" + "=" * 70)
print("OAUTH2 AUTHENTICATION TEST")
print("=" * 70)

# Get OAuth credentials from environment
oauth_client_id = os.getenv('EC3_OAUTH_CLIENT_ID')
oauth_client_secret = os.getenv('EC3_OAUTH_CLIENT_SECRET')
oauth_username = os.getenv('EC3_OAUTH_USERNAME')
oauth_password = os.getenv('EC3_OAUTH_PASSWORD')
oauth_scope = os.getenv('EC3_OAUTH_SCOPE', 'read')

print("\n1. Checking OAuth credentials from environment:")
print(f"   EC3_OAUTH_CLIENT_ID: {'✓ ' + oauth_client_id[:20] + '...' if oauth_client_id else '❌ NOT SET'}")
print(f"   EC3_OAUTH_CLIENT_SECRET: {'✓ SET (' + str(len(oauth_client_secret)) + ' chars)' if oauth_client_secret else '❌ NOT SET'}")
print(f"   EC3_OAUTH_USERNAME: {'✓ ' + oauth_username if oauth_username else '❌ NOT SET'}")
print(f"   EC3_OAUTH_PASSWORD: {'✓ SET (' + str(len(oauth_password)) + ' chars)' if oauth_password else '❌ NOT SET'}")
print(f"   EC3_OAUTH_SCOPE: {oauth_scope}")

# Check if all required credentials are present
if not all([oauth_client_id, oauth_client_secret, oauth_username, oauth_password]):
    print("\n❌ ERROR: OAuth credentials incomplete!")
    print("\nMissing:")
    if not oauth_client_id:
        print("  - EC3_OAUTH_CLIENT_ID")
    if not oauth_client_secret:
        print("  - EC3_OAUTH_CLIENT_SECRET")
    if not oauth_username:
        print("  - EC3_OAUTH_USERNAME")
    if not oauth_password:
        print("  - EC3_OAUTH_PASSWORD")

    print("\n.env file check:")
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
        oauth_lines = [l for l in lines if 'OAUTH' in l.upper() and not l.strip().startswith('#')]
        print(f"   Found {len(oauth_lines)} OAuth-related lines in .env")
        for line in oauth_lines:
            # Show variable name only
            if '=' in line:
                var_name = line.split('=')[0].strip()
                print(f"   - {var_name}")

    sys.exit(1)

print("\n✓ All OAuth credentials found!")

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Now import EC3Client
from mothra.agents.discovery.ec3_integration import EC3Client

# Build OAuth config
oauth_config = {
    'grant_type': 'password',
    'client_id': oauth_client_id,
    'client_secret': oauth_client_secret,
    'username': oauth_username,
    'password': oauth_password,
    'scope': oauth_scope,
}


async def test_oauth():
    """Test OAuth authentication."""

    print("\n2. Creating EC3Client with OAuth config...")

    # Create client with ONLY OAuth (no API key)
    client = EC3Client(
        oauth_config=oauth_config,
        api_key=None,  # Force OAuth only
        auto_load_credentials=False
    )

    print("   ✓ Client created")

    try:
        async with client as c:
            print(f"\n3. Client session started:")
            print(f"   - Has OAuth config: {bool(c.oauth_config)}")
            print(f"   - Has API key: {bool(c.api_key)}")
            print(f"   - Has access token: {bool(c.access_token)}")

            if not c.access_token:
                print("\n❌ Failed to acquire OAuth access token!")
                print("   This could mean:")
                print("   1. OAuth credentials are incorrect")
                print("   2. EC3 OAuth service is down")
                print("   3. Network connectivity issues")
                return False

            print(f"   - Access token: {c.access_token[:20]}...{c.access_token[-10:]}")

            print("\n4. Testing API access with OAuth token...")

            # Try to fetch some EPDs
            response = await c.search_epds(limit=5)
            results = response.get('results', [])
            count = response.get('count', 0)

            print(f"   - Results fetched: {len(results)}")
            print(f"   - Total available: {count}")

            if not results:
                print("\n⚠️  OAuth token acquired but no EPDs returned")
                print("   Your token might not have the right permissions")
                return False

            print("\n✓✓✓ OAuth authentication SUCCESS!")
            print("\nSample EPDs fetched with OAuth:")
            for i, epd in enumerate(results[:3], 1):
                name = epd.get('name', 'Unknown')
                epd_id = epd.get('id', 'Unknown')
                print(f"   {i}. {name} (ID: {epd_id})")

            return True

    except Exception as e:
        print(f"\n❌ OAuth test failed with error:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return False


print("\n" + "=" * 70)
success = asyncio.run(test_oauth())
print("=" * 70)

if success:
    print("\n🎉 OAuth authentication is working!")
    print("You can now use OAuth with the EPD loader.")
    sys.exit(0)
else:
    print("\n❌ OAuth authentication failed.")
    print("\nTroubleshooting steps:")
    print("1. Verify your credentials at: https://buildingtransparency.org/ec3/manage-apps")
    print("2. Check that your OAuth app has the correct permissions")
    print("3. Try regenerating your OAuth client secret")
    print("4. Make sure your .env file doesn't have extra quotes or spaces")
    sys.exit(1)
