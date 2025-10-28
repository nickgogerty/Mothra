#!/usr/bin/env python3
"""
Diagnose OAuth2 "invalid_client" error with EC3 API.

This script will help identify why the OAuth2 client credentials are being rejected.
"""

import asyncio
import os
import sys
from pathlib import Path

# Load .env first
from dotenv import load_dotenv
load_dotenv()

import aiohttp
import json


async def test_oauth_token_detailed():
    """Test OAuth2 token acquisition with detailed debugging."""
    print("=" * 80)
    print("OAUTH2 TOKEN ACQUISITION DIAGNOSTIC")
    print("=" * 80)

    # Load credentials
    client_id = os.getenv("EC3_OAUTH_CLIENT_ID")
    client_secret = os.getenv("EC3_OAUTH_CLIENT_SECRET")
    username = os.getenv("EC3_OAUTH_USERNAME")
    password = os.getenv("EC3_OAUTH_PASSWORD")
    scope = os.getenv("EC3_OAUTH_SCOPE", "read")

    print("\n1. CREDENTIALS CHECK")
    print("-" * 80)
    print(f"Client ID:     {client_id[:20]}... (length: {len(client_id)})")
    print(f"Client Secret: {client_secret[:20]}... (length: {len(client_secret)})")
    print(f"Username:      {username}")
    print(f"Password:      {'*' * len(password)} (length: {len(password)})")
    print(f"Scope:         {scope}")

    # Try token request with different configurations
    token_url = "https://buildingtransparency.org/api/oauth2/token"

    print(f"\n2. TOKEN REQUEST CONFIGURATIONS")
    print("-" * 80)
    print(f"Token URL: {token_url}")

    # Configuration 1: Standard password grant
    print("\n▶ Attempt 1: Standard OAuth2 Password Grant (form-encoded)")
    payload1 = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
        "scope": scope,
    }

    print(f"  Payload keys: {list(payload1.keys())}")
    result1 = await try_token_request(token_url, payload1, "application/x-www-form-urlencoded")

    if result1['success']:
        print(f"\n✓ SUCCESS! Token acquired")
        return result1

    # Configuration 2: Try without scope
    print("\n▶ Attempt 2: Without explicit scope")
    payload2 = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password,
    }
    result2 = await try_token_request(token_url, payload2, "application/x-www-form-urlencoded")

    if result2['success']:
        print(f"\n✓ SUCCESS! Token acquired")
        return result2

    # Configuration 3: Try with Basic Auth for client credentials
    print("\n▶ Attempt 3: Client credentials in Basic Auth header")
    import base64
    credentials = f"{client_id}:{client_secret}"
    b64_credentials = base64.b64encode(credentials.encode()).decode()

    payload3 = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": scope,
    }

    headers3 = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_credentials}"
    }

    result3 = await try_token_request(token_url, payload3, None, headers3)

    if result3['success']:
        print(f"\n✓ SUCCESS! Token acquired")
        return result3

    # Configuration 4: JSON body instead of form
    print("\n▶ Attempt 4: JSON body (non-standard)")
    result4 = await try_token_request(token_url, payload1, "application/json")

    if result4['success']:
        print(f"\n✓ SUCCESS! Token acquired")
        return result4

    print("\n" + "=" * 80)
    print("❌ ALL ATTEMPTS FAILED")
    print("=" * 80)
    print("\nPossible issues:")
    print("1. OAuth2 application 'mothratest' was deleted or disabled")
    print("2. Client ID or Client Secret are incorrect")
    print("3. The OAuth2 application doesn't have password grant enabled")
    print("4. Username/password are incorrect or account is disabled")
    print("5. EC3's OAuth implementation requires different parameters")

    print("\nNext steps:")
    print("1. Log into EC3: https://buildingtransparency.org/")
    print("2. Go to: https://buildingtransparency.org/ec3/manage-apps")
    print("3. Check if 'mothratest' application exists")
    print("4. Verify the Client ID and Client Secret match")
    print("5. Check if Password Grant flow is enabled")
    print("6. Try creating a new OAuth application")

    return None


async def try_token_request(url, payload, content_type, extra_headers=None):
    """Try a token request with given configuration."""
    try:
        headers = extra_headers.copy() if extra_headers else {}

        if content_type and "Content-Type" not in headers:
            headers["Content-Type"] = content_type

        # Prepare data based on content type
        if content_type == "application/json":
            data_kwargs = {"json": payload}
        else:
            data_kwargs = {"data": payload}

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, **data_kwargs, timeout=aiohttp.ClientTimeout(total=10)) as response:
                status = response.status
                text = await response.text()

                print(f"  Status: {status}")
                print(f"  Response: {text[:200]}")

                if status == 200:
                    try:
                        data = json.loads(text)
                        token = data.get("access_token")
                        expires_in = data.get("expires_in")

                        print(f"  ✓ Token: {token[:20]}...{token[-10:] if token else 'N/A'}")
                        print(f"  ✓ Expires: {expires_in}s")

                        return {
                            'success': True,
                            'token': token,
                            'expires_in': expires_in,
                            'data': data
                        }
                    except Exception as e:
                        print(f"  ✗ Failed to parse response: {e}")
                        return {'success': False, 'status': status, 'error': str(e)}
                else:
                    return {'success': False, 'status': status, 'error': text}

    except Exception as e:
        print(f"  ✗ Exception: {e}")
        return {'success': False, 'error': str(e)}


async def test_api_key_on_epd_endpoint():
    """Test if API key works on EPD endpoint."""
    print("\n" + "=" * 80)
    print("API KEY TEST ON EPD ENDPOINT")
    print("=" * 80)

    api_key = os.getenv("EC3_API_KEY")

    if not api_key:
        print("❌ No API key found")
        return False

    print(f"API Key: {api_key[:20]}...")

    url = "https://buildingtransparency.org/api/epds"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params={"limit": 1}) as response:
                status = response.status
                text = await response.text()

                print(f"Status: {status}")
                print(f"Response: {text[:300]}")

                if status == 200:
                    data = json.loads(text)
                    print(f"\n✓ API KEY WORKS on EPD endpoint!")
                    print(f"  Results: {len(data.get('results', []))}")
                    print(f"  Total: {data.get('count', 'unknown')}")
                    return True
                elif status == 401:
                    print(f"\n❌ API key rejected on EPD endpoint")
                    print(f"  This endpoint may require OAuth2 token specifically")
                    return False
                else:
                    print(f"\n⚠️  Unexpected status: {status}")
                    return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


async def main():
    """Run diagnostics."""
    # Test OAuth2
    oauth_result = await test_oauth_token_detailed()

    # Test API key on EPD endpoint
    api_key_result = await test_api_key_on_epd_endpoint()

    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print(f"OAuth2 Token Acquisition: {'✓ SUCCESS' if oauth_result and oauth_result.get('success') else '❌ FAILED'}")
    print(f"API Key on EPD Endpoint:  {'✓ WORKS' if api_key_result else '❌ FAILED'}")

    if api_key_result and not (oauth_result and oauth_result.get('success')):
        print("\n💡 RECOMMENDATION:")
        print("   The API key works on the EPD endpoint, so OAuth2 is not strictly required.")
        print("   However, the OAuth2 client credentials appear to be invalid.")
        print("   ")
        print("   You have two options:")
        print("   1. Fix the OAuth2 credentials in your EC3 account")
        print("   2. Use API key only (remove OAuth vars from .env)")


if __name__ == "__main__":
    asyncio.run(main())
