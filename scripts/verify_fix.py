"""
Verification script to test that SQLAlchemy metadata issue is fixed.
Run this after pulling the latest code to verify all imports work.
"""

import sys


def test_imports():
    """Test all critical imports that were failing before."""
    print("=" * 60)
    print("MOTHRA - Import Verification")
    print("=" * 60)
    print()

    tests = []

    # Test 1: Verification models
    print("1. Testing verification models...")
    try:
        from mothra.db.models_verification import (
            CarbonEntityVerification,
            Scope3Category,
        )

        print("   ✅ Verification models imported successfully")
        print(f"      - CarbonEntityVerification: {CarbonEntityVerification.__tablename__}")
        print(f"      - Scope3Category: {Scope3Category.__tablename__}")
        tests.append(True)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests.append(False)

    print()

    # Test 2: EC3 integration
    print("2. Testing EC3 integration...")
    try:
        from mothra.agents.discovery.ec3_integration import EC3Client, EC3EPDParser

        print("   ✅ EC3 integration imported successfully")
        print(f"      - EC3Client base URL: {EC3Client.BASE_URL}")
        tests.append(True)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests.append(False)

    print()

    # Test 3: Dataset discovery
    print("3. Testing dataset discovery...")
    try:
        from mothra.agents.discovery.dataset_discovery import (
            DataFileParser,
            DatasetDiscovery,
        )

        print("   ✅ Dataset discovery imported successfully")
        tests.append(True)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests.append(False)

    print()

    # Test 4: All DB models
    print("4. Testing complete DB model import chain...")
    try:
        from mothra.db import (
            Base,
            CarbonEntityVerification,
            DocumentChunk,
            Scope3Category,
        )

        print("   ✅ All DB models imported successfully")
        print(f"      - Base metadata tables: {len(Base.metadata.tables)}")
        tests.append(True)
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests.append(False)

    print()
    print("=" * 60)

    # Summary
    passed = sum(tests)
    total = len(tests)

    if passed == total:
        print(f"✅ SUCCESS: All {total} tests passed!")
        print("=" * 60)
        print()
        print("The SQLAlchemy 'metadata' issue is FIXED.")
        print()
        print("You can now run:")
        print("  python scripts/test_ec3_integration.py")
        print("  python scripts/import_ec3_epds.py")
        print("  python scripts/deep_crawl_real_datasets.py")
        print()
        return 0
    else:
        print(f"❌ FAILED: {total - passed}/{total} tests failed")
        print("=" * 60)
        print()
        print("Some imports are still broken. Check errors above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(test_imports())
