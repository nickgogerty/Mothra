#!/usr/bin/env python3
"""Show raw .env file contents."""

from pathlib import Path

env_path = Path(__file__).parent / '.env'

print("=" * 70)
print("RAW .ENV FILE CONTENTS")
print("=" * 70)
print(f"\nFile: {env_path}")
print(f"Exists: {env_path.exists()}")

if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"Total size: {len(content)} bytes")
    print(f"\nSearching for OAuth lines...\n")

    lines = content.split('\n')
    print(f"Total lines: {len(lines)}")

    # Show ALL lines that contain "OAUTH" (case insensitive)
    oauth_lines = []
    for i, line in enumerate(lines, 1):
        if 'oauth' in line.lower():
            oauth_lines.append((i, line))

    if oauth_lines:
        print(f"\nFound {len(oauth_lines)} lines containing 'oauth':")
        print("-" * 70)
        for line_num, line in oauth_lines:
            # Show line with visible special characters
            display_line = line.replace('\r', '\\r').replace('\t', '\\t')
            print(f"Line {line_num:3d}: {display_line}")
        print("-" * 70)
    else:
        print("\n❌ NO LINES CONTAINING 'OAUTH' FOUND!")
        print("\nShowing lines 10-25 (where OAuth should be):")
        print("-" * 70)
        for i in range(9, min(25, len(lines))):
            display_line = lines[i].replace('\r', '\\r').replace('\t', '\\t')
            print(f"Line {i+1:3d}: {display_line}")
        print("-" * 70)

    # Now test if python-dotenv can parse it
    print("\nTesting python-dotenv parsing...")
    from dotenv import dotenv_values

    env_dict = dotenv_values(env_path)
    print(f"Variables loaded by dotenv: {len(env_dict)}")

    # Show all variable names (not values)
    print("\nVariable names found:")
    for key in sorted(env_dict.keys()):
        if 'oauth' in key.lower():
            print(f"  ✓ {key}")
        else:
            print(f"    {key}")

    # Check specifically for OAuth vars
    oauth_vars = [
        'EC3_OAUTH_CLIENT_ID',
        'EC3_OAUTH_CLIENT_SECRET',
        'EC3_OAUTH_USERNAME',
        'EC3_OAUTH_PASSWORD',
        'EC3_OAUTH_SCOPE'
    ]

    print("\nChecking for specific OAuth variables:")
    for var in oauth_vars:
        value = env_dict.get(var)
        if value:
            if 'PASSWORD' in var or 'SECRET' in var:
                print(f"  ✓ {var}: [SET, {len(value)} chars]")
            else:
                print(f"  ✓ {var}: {value[:30]}...")
        else:
            print(f"  ❌ {var}: NOT FOUND")
else:
    print("❌ .env file does not exist!")

print("\n" + "=" * 70)
