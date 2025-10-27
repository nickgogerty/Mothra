"""Test import order issue with settings."""

import os
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("IMPORT ORDER TEST")
print("=" * 60)

# Check environment BEFORE any imports
print("\n1. Environment BEFORE load_dotenv:")
print(f"   EC3_API_KEY: {os.getenv('EC3_API_KEY', 'NOT SET')[:20] if os.getenv('EC3_API_KEY') else 'NOT SET'}")
print(f"   EC3_OAUTH_CLIENT_ID: {os.getenv('EC3_OAUTH_CLIENT_ID', 'NOT SET')[:20] if os.getenv('EC3_OAUTH_CLIENT_ID') else 'NOT SET'}")

# Load .env (simulating the script's approach)
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print("\n2. Loaded .env file")
else:
    print("\n2. .env file not found")

# Check environment AFTER load_dotenv
print("\n3. Environment AFTER load_dotenv:")
print(f"   EC3_API_KEY: {os.getenv('EC3_API_KEY', 'NOT SET')[:20] if os.getenv('EC3_API_KEY') else 'NOT SET'}")
print(f"   EC3_OAUTH_CLIENT_ID: {os.getenv('EC3_OAUTH_CLIENT_ID', 'NOT SET')[:20] if os.getenv('EC3_OAUTH_CLIENT_ID') else 'NOT SET'}")

# Now import settings (this will create the Settings instance)
print("\n4. Importing settings...")
from mothra.config import settings

# Check what settings sees
print("\n5. What settings sees:")
print(f"   settings.ec3_api_key: {settings.ec3_api_key[:20] if settings.ec3_api_key else 'NOT SET'}")
print(f"   settings.ec3_oauth_client_id: {settings.ec3_oauth_client_id[:20] if settings.ec3_oauth_client_id else 'NOT SET'}")
print(f"   settings.ec3_oauth_username: {settings.ec3_oauth_username or 'NOT SET'}")

# Now import EC3Client (which imports settings internally)
print("\n6. Importing EC3Client...")
from mothra.agents.discovery.ec3_integration import EC3Client

# Create client and check what it loads
print("\n7. Creating EC3Client...")
client = EC3Client()
print(f"   client.api_key: {client.api_key[:20] if client.api_key else 'NOT SET'}")
print(f"   client.oauth_config: {bool(client.oauth_config)}")
if client.oauth_config:
    print(f"   oauth_config keys: {client.oauth_config.keys()}")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
if client.oauth_config:
    print("✓ OAuth config loaded successfully")
elif client.api_key:
    print("⚠️  Only API key loaded (OAuth config missing)")
else:
    print("❌ No credentials loaded")
