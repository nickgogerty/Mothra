"""
Test EC3 API credentials to diagnose authentication issues.

This script will:
1. Show what credentials are loaded from .env
2. Test API key authentication with a simple request
3. Test OAuth2 authentication if configured
4. Validate credentials using the EC3Client
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import aiohttp
from dotenv import load_dotenv

from mothra.agents.discovery.ec3_integration import EC3Client
from mothra.utils.logging import get_logger

logger = get_logger(__name__)

# Load .env file
load_dotenv()


async def test_raw_api_key():
    """Test API key with a raw HTTP request."""
    print("\n" + "=" * 60)
    print("TEST 1: Raw API Key Test")
    print("=" * 60)

    api_key = os.getenv("EC3_API_KEY")

    if not api_key:
        print("❌ EC3_API_KEY not found in environment")
        return False

    print(f"✓ API Key loaded: {api_key[:10]}...{api_key[-4:]} (length: {len(api_key)})")

    # Test with a simple endpoint
    url = "https://buildingtransparency.org/api/epds"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }

    print(f"\nTesting endpoint: {url}")
    print(f"Authorization header: Bearer {api_key[:10]}...{api_key[-4:]}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params={"limit": 1}) as response:
                print(f"\nStatus: {response.status}")
                print(f"Headers: {dict(response.headers)}")

                if response.status == 200:
                    data = await response.json()
                    print(f"✓ Success! Got {len(data.get('results', []))} results")
                    print(f"  Total available: {data.get('count', 'unknown')}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Failed with status {response.status}")
                    print(f"Response: {text[:500]}")
                    return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


async def test_oauth2():
    """Test OAuth2 authentication."""
    print("\n" + "=" * 60)
    print("TEST 2: OAuth2 Test")
    print("=" * 60)

    client_id = os.getenv("EC3_OAUTH_CLIENT_ID")
    client_secret = os.getenv("EC3_OAUTH_CLIENT_SECRET")
    username = os.getenv("EC3_OAUTH_USERNAME")
    password = os.getenv("EC3_OAUTH_PASSWORD")

    if not all([client_id, client_secret, username, password]):
        print("⚠️  OAuth2 credentials not fully configured")
        print(f"   client_id: {'✓' if client_id else '❌'}")
        print(f"   client_secret: {'✓' if client_secret else '❌'}")
        print(f"   username: {'✓' if username else '❌'}")
        print(f"   password: {'✓' if password else '❌'}")
        return False

    print("✓ OAuth2 credentials loaded")
    print(f"  Client ID: {client_id[:10]}...{client_id[-4:]}")
    print(f"  Username: {username}")

    # Try to get token
    token_url = "https://buildingtransparency.org/api/oauth2/token"
    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
        "scope": os.getenv("EC3_OAUTH_SCOPE", "read"),
    }

    print(f"\nRequesting token from: {token_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                token_url,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                print(f"Status: {response.status}")

                if response.status == 200:
                    data = await response.json()
                    access_token = data.get("access_token")
                    expires_in = data.get("expires_in")
                    print(f"✓ Token acquired successfully!")
                    print(f"  Token: {access_token[:10]}...{access_token[-4:] if access_token else 'N/A'}")
                    print(f"  Expires in: {expires_in} seconds")

                    # Test the token
                    print("\nTesting token with EPDs endpoint...")
                    test_url = "https://buildingtransparency.org/api/epds"
                    async with session.get(
                        test_url,
                        headers={"Authorization": f"Bearer {access_token}"},
                        params={"limit": 1},
                    ) as test_response:
                        print(f"Status: {test_response.status}")
                        if test_response.status == 200:
                            test_data = await test_response.json()
                            print(f"✓ Token works! Got {len(test_data.get('results', []))} results")
                            return True
                        else:
                            text = await test_response.text()
                            print(f"❌ Token test failed: {text[:500]}")
                            return False
                else:
                    text = await response.text()
                    print(f"❌ Token request failed with status {response.status}")
                    print(f"Response: {text[:500]}")
                    return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


async def test_ec3_client():
    """Test the EC3Client class."""
    print("\n" + "=" * 60)
    print("TEST 3: EC3Client Test")
    print("=" * 60)

    try:
        async with EC3Client() as client:
            print(f"Client initialized")
            print(f"  Has OAuth config: {bool(client.oauth_config)}")
            print(f"  Has API key: {bool(client.api_key)}")
            print(f"  Has access token: {bool(client.access_token)}")

            # Check session headers
            if client.session:
                auth_header = client.session.headers.get("Authorization")
                if auth_header:
                    print(f"  Authorization header: {auth_header[:20]}...{auth_header[-10:]}")
                else:
                    print(f"  ❌ No Authorization header in session!")

            # Validate credentials
            print("\nValidating credentials...")
            validation = await client.validate_credentials()
            print(f"  Valid: {validation['valid']}")
            print(f"  Auth method: {validation['auth_method']}")
            print(f"  Message: {validation['message']}")

            if not validation['valid']:
                return False

            # Try fetching EPDs
            print("\nFetching EPDs...")
            response = await client.search_epds(limit=1)
            results = response.get("results", [])
            count = response.get("count", 0)

            print(f"  Results in this page: {len(results)}")
            print(f"  Total available: {count}")

            if results:
                print(f"✓ Successfully fetched EPDs!")
                return True
            else:
                print(f"⚠️  No results returned")
                return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("EC3 CREDENTIALS TEST SUITE")
    print("=" * 60)

    # Show environment variables
    print("\nEnvironment variables loaded:")
    print(f"  EC3_API_KEY: {'✓ ' + os.getenv('EC3_API_KEY', 'NOT SET')[:20] + '...' if os.getenv('EC3_API_KEY') else '❌ NOT SET'}")
    print(f"  EC3_OAUTH_CLIENT_ID: {'✓ ' + os.getenv('EC3_OAUTH_CLIENT_ID', 'NOT SET')[:20] + '...' if os.getenv('EC3_OAUTH_CLIENT_ID') else '❌ NOT SET'}")
    print(f"  EC3_OAUTH_CLIENT_SECRET: {'✓ SET' if os.getenv('EC3_OAUTH_CLIENT_SECRET') else '❌ NOT SET'}")
    print(f"  EC3_OAUTH_USERNAME: {'✓ ' + os.getenv('EC3_OAUTH_USERNAME', 'NOT SET') if os.getenv('EC3_OAUTH_USERNAME') else '❌ NOT SET'}")
    print(f"  EC3_OAUTH_PASSWORD: {'✓ SET' if os.getenv('EC3_OAUTH_PASSWORD') else '❌ NOT SET'}")

    # Run tests
    results = []

    # Test 1: Raw API key
    results.append(("Raw API Key", await test_raw_api_key()))

    # Test 2: OAuth2
    results.append(("OAuth2", await test_oauth2()))

    # Test 3: EC3Client
    results.append(("EC3Client", await test_ec3_client()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, success in results:
        status = "✓ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")

    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    if not any(result[1] for result in results):
        print("\n❌ All tests failed. Possible issues:")
        print("   1. API key is invalid or expired")
        print("   2. OAuth2 credentials are incorrect")
        print("   3. Network/firewall issues preventing API access")
        print("   4. EC3 API endpoint has changed")
        print("\nNext steps:")
        print("   - Verify API key at: https://buildingtransparency.org/ec3/manage-apps/keys")
        print("   - Check if you can access the API in a browser while logged in")
        print("   - Try generating a new API key")
    elif results[0][1]:  # Raw API key works
        print("\n✓ API key authentication is working!")
        print("  You can fetch EPDs from EC3")
    elif results[1][1]:  # OAuth2 works
        print("\n✓ OAuth2 authentication is working!")
        print("  You can fetch EPDs from EC3")
    else:
        print("\n⚠️  Authentication tests passed but EC3Client failed")
        print("  This might be a bug in the client code")


if __name__ == "__main__":
    asyncio.run(main())
