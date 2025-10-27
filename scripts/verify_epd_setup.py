#!/usr/bin/env python3
"""
EPD Setup Verification Script
==============================
Checks that all dependencies and configurations are correct before running the EPD loader.

Usage:
    python scripts/verify_epd_setup.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"  ✗ Python {version.major}.{version.minor} is too old")
        print(f"  Required: Python 3.9 or higher")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_imports():
    """Check that all required packages are installed."""
    print("\nChecking Python packages...")

    packages = [
        ('asyncpg', 'PostgreSQL async driver'),
        ('sqlalchemy', 'Database ORM'),
        ('pgvector', 'Vector database support'),
        ('aiohttp', 'Async HTTP client'),
        ('sentence_transformers', 'Embedding generation'),
        ('torch', 'PyTorch for transformers'),
        ('pydantic', 'Data validation'),
    ]

    all_ok = True
    for package, description in packages:
        try:
            __import__(package)
            print(f"  ✓ {package:25s} - {description}")
        except ImportError:
            print(f"  ✗ {package:25s} - {description} (MISSING)")
            all_ok = False

    return all_ok


def check_env_variables():
    """Check environment variables."""
    print("\nChecking environment variables...")

    has_api_key = os.getenv('EC3_API_KEY')
    has_oauth_username = os.getenv('EC3_OAUTH_USERNAME')
    has_oauth_password = os.getenv('EC3_OAUTH_PASSWORD')

    if has_api_key:
        print(f"  ✓ EC3_API_KEY is set")
        print(f"    Value: {has_api_key[:10]}..." if len(has_api_key) > 10 else has_api_key)
        return True
    elif has_oauth_username and has_oauth_password:
        print(f"  ✓ EC3 OAuth credentials are set")
        print(f"    Username: {has_oauth_username}")
        return True
    else:
        print(f"  ✗ EC3 credentials not found")
        print(f"    Please set either:")
        print(f"      - EC3_API_KEY")
        print(f"    or:")
        print(f"      - EC3_OAUTH_USERNAME and EC3_OAUTH_PASSWORD")
        print(f"    Get API key from: https://buildingtransparency.org/api")
        return False


def check_database():
    """Check database connection."""
    print("\nChecking database connection...")

    try:
        import asyncio
        from mothra.db.session import AsyncSessionLocal
        from sqlalchemy import text

        async def test_connection():
            try:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(text("SELECT version()"))
                    version = result.scalar()
                    print(f"  ✓ PostgreSQL connected")
                    print(f"    Version: {version.split(',')[0]}")

                    # Check pgvector extension
                    result = await session.execute(
                        text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                    )
                    vector_version = result.scalar()
                    if vector_version:
                        print(f"  ✓ pgvector extension installed")
                        print(f"    Version: {vector_version}")
                        return True
                    else:
                        print(f"  ✗ pgvector extension not installed")
                        print(f"    Run: CREATE EXTENSION vector;")
                        return False

            except Exception as e:
                print(f"  ✗ Database connection failed: {e}")
                return False

        return asyncio.run(test_connection())

    except Exception as e:
        print(f"  ✗ Cannot import database modules: {e}")
        return False


def check_models():
    """Check that database models can be imported."""
    print("\nChecking database models...")

    try:
        from mothra.db.models import CarbonEntity, EmissionFactor, DataSource
        print(f"  ✓ CarbonEntity model")

        from mothra.db.models_verification import CarbonEntityVerification
        print(f"  ✓ CarbonEntityVerification model")

        from mothra.db.models_chunks import DocumentChunk
        print(f"  ✓ DocumentChunk model")

        return True

    except Exception as e:
        print(f"  ✗ Cannot import models: {e}")
        return False


def check_ec3_client():
    """Check EC3 client."""
    print("\nChecking EC3 client...")

    try:
        from mothra.agents.discovery.ec3_integration import EC3Client, EC3EPDParser
        print(f"  ✓ EC3Client available")

        client = EC3Client()
        print(f"  ✓ EC3Client instantiated")

        return True

    except Exception as e:
        print(f"  ✗ Cannot import EC3Client: {e}")
        return False


def check_vector_manager():
    """Check vector manager."""
    print("\nChecking vector manager...")

    try:
        from mothra.agents.embedding.vector_manager import VectorManager
        print(f"  ✓ VectorManager available")

        manager = VectorManager()
        print(f"  ✓ VectorManager instantiated")
        print(f"    Model: {manager.model_name}")
        print(f"    Dimensions: {manager.embedding_dim}")

        return True

    except Exception as e:
        print(f"  ✗ Cannot import VectorManager: {e}")
        return False


def check_text_chunker():
    """Check text chunker."""
    print("\nChecking text chunker...")

    try:
        from mothra.utils.text_chunker import TextChunker
        print(f"  ✓ TextChunker available")

        chunker = TextChunker()
        print(f"  ✓ TextChunker instantiated")
        print(f"    Chunk size: {chunker.chunk_size}")
        print(f"    Overlap: {chunker.chunk_overlap}")

        return True

    except Exception as e:
        print(f"  ✗ Cannot import TextChunker: {e}")
        return False


def main():
    """Run all checks."""
    print("="*80)
    print("EPD VECTOR STORE - SETUP VERIFICATION")
    print("="*80)

    checks = [
        ('Python Version', check_python_version),
        ('Python Packages', check_imports),
        ('Environment Variables', check_env_variables),
        ('Database Connection', check_database),
        ('Database Models', check_models),
        ('EC3 Client', check_ec3_client),
        ('Vector Manager', check_vector_manager),
        ('Text Chunker', check_text_chunker),
    ]

    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} check failed with exception: {e}")
            results[name] = False

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    all_passed = True
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8s} - {name}")
        if not passed:
            all_passed = False

    print("="*80)

    if all_passed:
        print("\n✓ All checks passed! You're ready to load EPDs.")
        print("\nRun the loader with:")
        print("  ./scripts/run_epd_loader.sh --limit 100  # Test with 100 EPDs")
        print("  ./scripts/run_epd_loader.sh               # Load all EPDs")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
