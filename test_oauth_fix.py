#!/usr/bin/env python3
"""Test script to verify EC3 OAuth2 credentials are properly loaded."""

import asyncio
import sys
import os

# Ensure we're in the right directory
os.chdir('/home/user/Mothra')
sys.path.insert(0, '/home/user/Mothra')

# Import required modules directly
from mothra.config.settings import get_settings

async def test_credentials():
    """Test that EC3 credentials are properly loaded."""
    print("=" * 80)
    print("EC3 CREDENTIAL LOADING TEST")
    print("=" * 80)

    # Test 1: Check settings
    print("\n1. Checking settings...")
    settings = get_settings()

    print(f"   EC3_API_KEY: {'✓ Present' if settings.ec3_api_key else '✗ Missing'}")
    print(f"   EC3_OAUTH_CLIENT_ID: {'✓ Present' if settings.ec3_oauth_client_id else '✗ Missing'}")
    print(f"   EC3_OAUTH_CLIENT_SECRET: {'✓ Present' if settings.ec3_oauth_client_secret else '✗ Missing'}")
    print(f"   EC3_OAUTH_USERNAME: {'✓ Present' if settings.ec3_oauth_username else '✗ Missing'}")
    print(f"   EC3_OAUTH_PASSWORD: {'✓ Present' if settings.ec3_oauth_password else '✗ Missing'}")
    print(f"   EC3_OAUTH_SCOPE: {settings.ec3_oauth_scope}")

    # Test 2: Import EC3Client
    print("\n2. Importing EC3Client...")
    try:
        from mothra.agents.discovery.ec3_integration import EC3Client
        print("   ✓ EC3Client imported successfully")
    except Exception as e:
        print(f"   ✗ Failed to import EC3Client: {e}")
        return False

    # Test 3: Initialize EC3Client
    print("\n3. Initializing EC3Client...")
    try:
        client = EC3Client()
        print("   ✓ EC3Client initialized")
        print(f"   - API Key present: {'✓' if client.api_key else '✗'}")
        print(f"   - OAuth config present: {'✓' if client.oauth_config else '✗'}")

        if client.oauth_config:
            print(f"   - OAuth grant type: {client.oauth_config.get('grant_type')}")
            print(f"   - OAuth client_id: {client.oauth_config.get('client_id')[:20]}...")
            print(f"   - OAuth username: {client.oauth_config.get('username')}")
        else:
            print("   ✗ ERROR: OAuth config not loaded!")
            return False

    except Exception as e:
        print(f"   ✗ Failed to initialize EC3Client: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Test context manager entry and OAuth token acquisition
    print("\n4. Testing OAuth token acquisition...")
    try:
        async with client as c:
            print(f"   ✓ Context manager entered")
            print(f"   - Session created: {'✓' if c.session else '✗'}")
            print(f"   - Access token acquired: {'✓' if c.access_token else '✗'}")

            if c.access_token:
                print(f"   - Token preview: {c.access_token[:40]}...")

            # Test 5: Validate credentials
            print("\n5. Validating credentials with EC3 API...")
            result = await c.validate_credentials()

            print(f"   - Valid: {'✓' if result.get('valid') else '✗'}")
            print(f"   - Auth method: {result.get('auth_method')}")
            print(f"   - Message: {result.get('message')}")

            if result.get('valid'):
                print(f"   - Test endpoint: {result.get('test_endpoint')}")
                print(f"   - Test result count: {result.get('test_result', {}).get('count', 'N/A')}")

            return result.get('valid')

    except Exception as e:
        print(f"   ✗ Error during OAuth flow: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\nRunning EC3 OAuth2 credential test...\n")
    success = asyncio.run(test_credentials())

    print("\n" + "=" * 80)
    if success:
        print("✓ ALL TESTS PASSED - OAuth2 credentials are working!")
        print("=" * 80)
        sys.exit(0)
    else:
        print("✗ TESTS FAILED - Check the errors above")
        print("=" * 80)
        sys.exit(1)
