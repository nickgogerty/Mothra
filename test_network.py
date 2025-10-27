"""Test network connectivity from Python."""

import asyncio
import socket

import aiohttp


async def test_dns():
    """Test DNS resolution."""
    print("Testing DNS resolution...")
    try:
        # Test basic socket DNS
        print("\n1. Socket DNS lookup:")
        ip = socket.gethostbyname("buildingtransparency.org")
        print(f"   ✓ buildingtransparency.org resolves to: {ip}")
    except Exception as e:
        print(f"   ❌ Socket DNS failed: {e}")

    try:
        # Test getaddrinfo (more comprehensive)
        print("\n2. getaddrinfo lookup:")
        result = socket.getaddrinfo("buildingtransparency.org", 443, socket.AF_INET)
        for item in result[:3]:
            print(f"   ✓ {item}")
    except Exception as e:
        print(f"   ❌ getaddrinfo failed: {e}")


async def test_aiohttp_with_connector():
    """Test aiohttp with different connector settings."""
    print("\n3. Testing aiohttp with custom DNS:")

    # Try with family=0 (AF_UNSPEC) to allow both IPv4 and IPv6
    try:
        connector = aiohttp.TCPConnector(family=socket.AF_INET, force_close=True)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get("https://buildingtransparency.org/api/epds?limit=1") as response:
                print(f"   ✓ Status with AF_INET: {response.status}")
    except Exception as e:
        print(f"   ❌ AF_INET failed: {e}")

    # Try with default connector
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://buildingtransparency.org/api/epds?limit=1") as response:
                print(f"   ✓ Status with default: {response.status}")
    except Exception as e:
        print(f"   ❌ Default failed: {e}")


async def test_with_ip():
    """Test direct IP connection."""
    print("\n4. Testing with direct IP:")

    # Get IP first
    try:
        ip = socket.gethostbyname("buildingtransparency.org")
        print(f"   IP: {ip}")

        async with aiohttp.ClientSession() as session:
            # Need to set Host header when using IP
            headers = {"Host": "buildingtransparency.org"}
            async with session.get(f"https://{ip}/api/epds?limit=1", headers=headers, ssl=False) as response:
                print(f"   ✓ Status with IP: {response.status}")
    except Exception as e:
        print(f"   ❌ IP connection failed: {e}")


async def main():
    """Run all network tests."""
    print("=" * 60)
    print("PYTHON NETWORK DIAGNOSTIC")
    print("=" * 60)

    await test_dns()
    await test_aiohttp_with_connector()
    await test_with_ip()


if __name__ == "__main__":
    asyncio.run(main())
