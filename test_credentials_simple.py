#!/usr/bin/env python3
"""
Simple EC3 Credentials Test
============================
This script tests your EC3 API credentials in the correct order.
Run from project root: python scripts/test_credentials_simple.py
"""

import asyncio
import os
import sys
from pathlib import Path

# STEP 1: Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# STEP 2: Load .env BEFORE importing any mothra modules
print("=" * 70)
print("EC3 CREDENTIALS TEST")
print("=" * 70)

from dotenv import load_dotenv
env_path = project_root / '.env'
print(f"\n1. Loading .env from: {env_path}")
if env_path.exists():
    load_dotenv(env_path, override=True)
    print("   ✓ .env file loaded")
else:
    print(f"   ❌ .env file not found!")
    sys.exit(1)

# STEP 3: Verify environment variables are set
print("\n2. Checking environment variables:")
api_key = os.getenv('EC3_API_KEY')
oauth_client_id = os.getenv('EC3_OAUTH_CLIENT_ID')
oauth_client_secret = os.getenv('EC3_OAUTH_CLIENT_SECRET')
oauth_username = os.getenv('EC3_OAUTH_USERNAME')
oauth_password = os.getenv('EC3_OAUTH_PASSWORD')

print(f"   EC3_API_KEY: {'✓ ' + api_key[:15] + '...' if api_key else '❌ NOT SET'}")
print(f"   EC3_OAUTH_CLIENT_ID: {'✓ ' + oauth_client_id[:15] + '...' if oauth_client_id else '❌ NOT SET'}")
print(f"   EC3_OAUTH_CLIENT_SECRET: {'✓ SET' if oauth_client_secret else '❌ NOT SET'}")
print(f"   EC3_OAUTH_USERNAME: {'✓ ' + oauth_username if oauth_username else '❌ NOT SET'}")
print(f"   EC3_OAUTH_PASSWORD: {'✓ SET' if oauth_password else '❌ NOT SET'}")

# STEP 4: Import mothra modules (now settings will see the env vars)
print("\n3. Importing mothra modules...")
from mothra.agents.discovery.ec3_integration import EC3Client

# STEP 5: Test credentials
async def test_credentials():
    print("\n4. Testing credentials with EC3 API...")

    try:
        async with EC3Client() as client:
            print(f"   Client created:")
            print(f"   - Has API key: {bool(client.api_key)}")
            print(f"   - Has OAuth config: {bool(client.oauth_config)}")
            print(f"   - Has access token: {bool(client.access_token)}")

            # Validate
            print("\n5. Validating credentials...")
            result = await client.validate_credentials()

            print(f"   Valid: {result['valid']}")
            print(f"   Auth method: {result['auth_method']}")
            print(f"   Message: {result['message']}")

            if not result['valid']:
                print("\n❌ CREDENTIALS INVALID")
                print("\nTroubleshooting:")
                print("1. Check your API key at: https://buildingtransparency.org/ec3/manage-apps/keys")
                print("2. Verify OAuth credentials are correct")
                print("3. Make sure your account has API access enabled")
                return False

            # Try fetching a small sample
            print("\n6. Fetching sample EPDs...")
            response = await client.search_epds(limit=5)
            results = response.get('results', [])
            total = response.get('count', 0)

            print(f"   Results: {len(results)} EPDs")
            print(f"   Total available: {total}")

            if results:
                print("\n✓✓✓ SUCCESS! Your credentials work!")
                print(f"\nSample EPDs:")
                for i, epd in enumerate(results[:3], 1):
                    name = epd.get('name', 'Unknown')
                    epd_id = epd.get('id', 'Unknown')
                    print(f"   {i}. {name} (ID: {epd_id})")
                return True
            else:
                print("\n⚠️  Credentials valid but no EPDs returned")
                print("   This might be a permissions issue")
                return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run test
print("\n" + "=" * 70)
success = asyncio.run(test_credentials())
print("=" * 70)

if success:
    print("\n🎉 Your EC3 credentials are working correctly!")
    print("You can now run the EPD loader script.")
    sys.exit(0)
else:
    print("\n❌ Credential test failed. Please fix the issues above.")
    sys.exit(1)
