#!/usr/bin/env python3
"""Diagnose .env file loading issues."""

import os
from pathlib import Path

# Method 1: Raw file reading
print("=" * 70)
print("DIAGNOSING .ENV FILE")
print("=" * 70)

env_path = Path(__file__).parent / '.env'
print(f"\n1. Reading .env file directly: {env_path}")
if env_path.exists():
    with open(env_path, 'r') as f:
        lines = f.readlines()

    print(f"   Total lines: {len(lines)}")
    print("\n   OAuth-related lines:")
    for i, line in enumerate(lines, 1):
        if 'OAUTH' in line.upper() and not line.strip().startswith('#'):
            # Show line number and content, hiding password value
            if 'PASSWORD' in line.upper():
                print(f"   Line {i:2d}: EC3_OAUTH_PASSWORD=[HIDDEN]")
            else:
                print(f"   Line {i:2d}: {line.rstrip()}")
else:
    print("   ❌ .env file not found!")

# Method 2: Using python-dotenv
print("\n2. Loading with python-dotenv:")
from dotenv import load_dotenv, dotenv_values

# Load into environment
load_dotenv(env_path, override=True)

# Also get as dict
env_dict = dotenv_values(env_path)

oauth_vars = [
    'EC3_OAUTH_CLIENT_ID',
    'EC3_OAUTH_CLIENT_SECRET',
    'EC3_OAUTH_USERNAME',
    'EC3_OAUTH_PASSWORD',
    'EC3_OAUTH_SCOPE'
]

print("\n   From os.environ:")
for var in oauth_vars:
    value = os.getenv(var)
    if value:
        if 'PASSWORD' in var or 'SECRET' in var:
            print(f"   {var}: ✓ SET (length: {len(value)})")
        else:
            print(f"   {var}: {value[:30]}...")
    else:
        print(f"   {var}: ❌ NOT SET")

print("\n   From dotenv_values dict:")
for var in oauth_vars:
    value = env_dict.get(var)
    if value:
        if 'PASSWORD' in var or 'SECRET' in var:
            print(f"   {var}: ✓ SET (length: {len(value)})")
        else:
            print(f"   {var}: {value[:30]}...")
    else:
        print(f"   {var}: ❌ NOT SET")

# Method 3: Check for encoding issues
print("\n3. Checking for encoding/formatting issues:")
for var in oauth_vars:
    value = os.getenv(var)
    if value:
        has_quotes = value.startswith('"') or value.startswith("'")
        has_spaces = value.strip() != value
        print(f"   {var}:")
        print(f"      - Has surrounding quotes: {has_quotes}")
        print(f"      - Has leading/trailing spaces: {has_spaces}")
        if var == 'EC3_OAUTH_PASSWORD':
            # Check if quotes are included in the value
            print(f"      - First char: {repr(value[0]) if value else 'N/A'}")
            print(f"      - Last char: {repr(value[-1]) if value else 'N/A'}")

# Method 4: Test with pydantic Settings
print("\n4. Testing with pydantic Settings:")
import sys
sys.path.insert(0, str(Path(__file__).parent))

from pydantic_settings import BaseSettings
from pydantic import Field

class TestSettings(BaseSettings):
    """Test settings."""
    model_config = {
        'env_file': str(env_path),
        'env_file_encoding': 'utf-8',
        'case_sensitive': False,
        'extra': 'ignore',
    }

    ec3_oauth_client_id: str | None = Field(default=None)
    ec3_oauth_client_secret: str | None = Field(default=None)
    ec3_oauth_username: str | None = Field(default=None)
    ec3_oauth_password: str | None = Field(default=None)
    ec3_oauth_scope: str = Field(default="read")

try:
    test_settings = TestSettings()
    print("   Pydantic Settings loaded:")
    print(f"   - client_id: {'✓ ' + test_settings.ec3_oauth_client_id[:20] + '...' if test_settings.ec3_oauth_client_id else '❌ NOT SET'}")
    print(f"   - client_secret: {'✓ SET' if test_settings.ec3_oauth_client_secret else '❌ NOT SET'}")
    print(f"   - username: {'✓ ' + test_settings.ec3_oauth_username if test_settings.ec3_oauth_username else '❌ NOT SET'}")
    print(f"   - password: {'✓ SET' if test_settings.ec3_oauth_password else '❌ NOT SET'}")
    print(f"   - scope: {test_settings.ec3_oauth_scope}")
except Exception as e:
    print(f"   ❌ Error loading settings: {e}")

print("\n" + "=" * 70)
