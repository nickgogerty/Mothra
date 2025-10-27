"""
EC3 API Key Setup Helper

Checks if EC3 API key is configured and helps you set it up.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_ec3_api_key():
    """Check if EC3 API key is configured."""
    print("=" * 80)
    print("EC3 API KEY CHECKER")
    print("=" * 80)

    # Check environment variable
    api_key = os.getenv("EC3_API_KEY")

    if api_key:
        print("\n✅ EC3_API_KEY is SET")
        print(f"   Key: {api_key[:10]}...{api_key[-4:]}")
        print("\nYou're ready to import EPDs!")
        print("\nNext step:")
        print("  python scripts/bulk_import_epds.py")
        return True
    else:
        print("\n❌ EC3_API_KEY is NOT SET")
        print("\nThe EC3 API requires authentication to access EPD data.")
        print("\n" + "=" * 80)
        print("HOW TO GET YOUR FREE API KEY")
        print("=" * 80)

        print("\n1️⃣  Create Account (Free)")
        print("   Visit: https://buildingtransparency.org/ec3/")
        print("   Click: Sign Up")

        print("\n2️⃣  Generate API Key")
        print("   After login, go to:")
        print("   • Click your profile icon (top right)")
        print("   • Settings → Manage Apps → API Keys")
        print("   • Click: 'Create New API Key'")
        print("   • Copy the key (starts with 'sk_live_')")

        print("\n3️⃣  Set API Key")
        print("\n   Option A: Temporary (current session only)")
        print("   ─────────────────────────────────────────")
        print("   export EC3_API_KEY='your-key-here'")

        print("\n   Option B: Permanent (add to .env file)")
        print("   ─────────────────────────────────────────")
        print("   echo 'EC3_API_KEY=your-key-here' >> .env")

        print("\n4️⃣  Verify Setup")
        print("   python scripts/check_ec3_key.py")

        print("\n" + "=" * 80)
        print("WHY YOU NEED THIS")
        print("=" * 80)

        print("\nThe EC3 database has:")
        print("  • 90,000+ verified EPDs")
        print("  • Construction materials (concrete, steel, wood, etc.)")
        print("  • Full verification data (ISO 14067, EN 15804)")
        print("  • Third-party verified carbon footprints")

        print("\nWithout the API key:")
        print("  ❌ Cannot import EPDs")
        print("  ❌ Cannot reach 100k entity goal via EC3")

        print("\nWith the API key:")
        print("  ✅ Import 90,000+ verified EPDs")
        print("  ✅ Reach 100k entities in ~30 minutes")
        print("  ✅ Professional-grade carbon verification data")

        print("\n" + "=" * 80)
        print("ALTERNATIVE DATA SOURCES")
        print("=" * 80)

        print("\nWhile you get your EC3 key, you can still grow the dataset:")
        print("\n1. Government Datasets (No API key needed)")
        print("   python scripts/deep_crawl_real_datasets.py")
        print("   • EPA GHGRP: 50,000+ facility records")
        print("   • EU ETS: 10,000+ facility records")
        print("   • UK DEFRA: 2,000+ emission factors")

        print("\n2. Research Datasets (Public)")
        print("   • EXIOBASE: Multi-regional I/O database")
        print("   • USEEIO: US environmental I/O model")

        print("\n" + "=" * 80)

        return False


if __name__ == "__main__":
    has_key = check_ec3_api_key()

    if not has_key:
        print("\n💡 Quick Start:")
        print("   1. Get API key from: https://buildingtransparency.org/ec3/")
        print("   2. Run: export EC3_API_KEY='your-key'")
        print("   3. Run: python scripts/check_ec3_key.py")
        print("   4. Run: python scripts/bulk_import_epds.py")
        print()
        sys.exit(1)
    else:
        sys.exit(0)
