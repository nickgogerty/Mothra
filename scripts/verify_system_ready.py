#!/usr/bin/env python3
"""
System Readiness Verification Script
=====================================
Verifies that all components are properly configured and ready for EPD loading.

Checks:
- Database connectivity and configuration
- pgvector extension installation
- Required tables exist
- EC3 API credentials are valid
- Embedding model is available
- Sufficient disk space
- Python dependencies

Usage:
    python scripts/verify_system_ready.py
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment from {env_path}\n")
    else:
        print(f"⚠ Warning: .env file not found at {env_path}\n")
except ImportError:
    print("⚠ Warning: python-dotenv not installed\n")


class SystemVerifier:
    """Verifies system readiness for EPD loading."""

    def __init__(self):
        self.checks_passed = 0
        self.checks_failed = 0
        self.warnings = 0

    def print_header(self, title: str):
        """Print a formatted header."""
        print(f"\n{'=' * 70}")
        print(f"{title:^70}")
        print(f"{'=' * 70}\n")

    def print_check(self, name: str, passed: bool, message: str = "", warning: bool = False):
        """Print a check result."""
        if passed:
            symbol = "✓"
            self.checks_passed += 1
        elif warning:
            symbol = "⚠"
            self.warnings += 1
        else:
            symbol = "✗"
            self.checks_failed += 1

        status = "PASS" if passed else ("WARN" if warning else "FAIL")
        print(f"{symbol} {name:40s} [{status}]")
        if message:
            print(f"  → {message}")

    async def check_database(self) -> bool:
        """Check database connectivity and configuration."""
        self.print_header("DATABASE CHECKS")

        try:
            from sqlalchemy.ext.asyncio import create_async_engine
            from sqlalchemy import text

            db_url = os.getenv('DATABASE_URL', 'postgresql+asyncpg://mothra:changeme@localhost:5432/mothra')
            engine = create_async_engine(db_url)

            try:
                async with engine.connect() as conn:
                    # Test connection
                    result = await conn.execute(text('SELECT version()'))
                    version = result.scalar()
                    self.print_check("Database connection", True, f"PostgreSQL: {version[:50]}...")

                    # Check pgvector extension
                    result = await conn.execute(text(
                        "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector')"
                    ))
                    has_pgvector = result.scalar()
                    self.print_check(
                        "pgvector extension",
                        has_pgvector,
                        "pgvector installed and ready" if has_pgvector else "pgvector NOT installed - run migrations"
                    )

                    # Check required tables
                    required_tables = [
                        'carbon_entities',
                        'carbon_entity_verification',
                        'document_chunks',
                        'emission_factors',
                        'data_sources'
                    ]

                    for table in required_tables:
                        result = await conn.execute(text(
                            f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='{table}')"
                        ))
                        exists = result.scalar()
                        self.print_check(
                            f"Table: {table}",
                            exists,
                            "Table exists" if exists else "Table missing - run migrations"
                        )

                    # Check database size
                    result = await conn.execute(text(
                        "SELECT pg_size_pretty(pg_database_size(current_database()))"
                    ))
                    db_size = result.scalar()
                    self.print_check("Database size", True, f"Current size: {db_size}")

                    # Check available connections
                    result = await conn.execute(text(
                        "SELECT count(*) FROM pg_stat_activity"
                    ))
                    active_connections = result.scalar()
                    result = await conn.execute(text(
                        "SHOW max_connections"
                    ))
                    max_connections = int(result.scalar())
                    self.print_check(
                        "Database connections",
                        active_connections < max_connections * 0.8,
                        f"{active_connections}/{max_connections} connections in use",
                        warning=(active_connections >= max_connections * 0.8)
                    )

                await engine.dispose()
                return True

            except Exception as e:
                self.print_check("Database connection", False, f"Error: {e}")
                return False

        except ImportError as e:
            self.print_check("Database dependencies", False, f"Missing dependencies: {e}")
            return False

    async def check_ec3_credentials(self) -> bool:
        """Check EC3 API credentials."""
        self.print_header("EC3 API CREDENTIALS")

        try:
            from mothra.agents.discovery.ec3_integration import EC3Client

            # Check environment variables
            has_api_key = bool(os.getenv('EC3_API_KEY'))
            has_oauth_client_id = bool(os.getenv('EC3_OAUTH_CLIENT_ID'))
            has_oauth_secret = bool(os.getenv('EC3_OAUTH_CLIENT_SECRET'))
            has_oauth_username = bool(os.getenv('EC3_OAUTH_USERNAME'))
            has_oauth_password = bool(os.getenv('EC3_OAUTH_PASSWORD'))

            self.print_check("EC3 API Key", has_api_key, "API key found" if has_api_key else "No API key configured")
            self.print_check(
                "EC3 OAuth credentials",
                has_oauth_client_id and has_oauth_secret,
                "OAuth client credentials found" if (has_oauth_client_id and has_oauth_secret) else "OAuth not configured"
            )
            self.print_check(
                "EC3 OAuth user credentials",
                has_oauth_username and has_oauth_password,
                "OAuth user credentials found" if (has_oauth_username and has_oauth_password) else "User credentials not configured"
            )

            # Test actual API connection
            if has_api_key or (has_oauth_client_id and has_oauth_secret):
                print("\n  Testing EC3 API connection...")
                try:
                    client = EC3Client()
                    async with client as c:
                        validation = await c.validate_credentials()
                        if validation.get('valid'):
                            auth_method = validation.get('auth_method', 'unknown')
                            self.print_check(
                                "EC3 API connectivity",
                                True,
                                f"Successfully authenticated using {auth_method}"
                            )
                            return True
                        else:
                            self.print_check(
                                "EC3 API connectivity",
                                False,
                                f"Authentication failed: {validation.get('message', 'Unknown error')}"
                            )
                            return False
                except Exception as e:
                    self.print_check("EC3 API connectivity", False, f"Connection error: {e}")
                    return False
            else:
                self.print_check("EC3 API connectivity", False, "No credentials configured")
                return False

        except ImportError as e:
            self.print_check("EC3 integration", False, f"Missing dependencies: {e}")
            return False

    def check_embedding_model(self) -> bool:
        """Check embedding model availability."""
        self.print_header("EMBEDDING MODEL")

        try:
            from sentence_transformers import SentenceTransformer
            import torch

            # Check PyTorch
            self.print_check("PyTorch", True, f"Version: {torch.__version__}")

            # Check CUDA availability
            cuda_available = torch.cuda.is_available()
            self.print_check(
                "CUDA GPU",
                cuda_available,
                f"CUDA available: {torch.cuda.get_device_name(0)}" if cuda_available else "No GPU - will use CPU (slower)",
                warning=not cuda_available
            )

            # Check model
            model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            print(f"\n  Loading model: {model_name}...")
            try:
                model = SentenceTransformer(model_name)
                self.print_check(
                    "Embedding model",
                    True,
                    f"Model loaded successfully: {model_name}"
                )

                # Test encoding
                test_text = "This is a test sentence for embedding."
                embedding = model.encode(test_text)
                expected_dim = int(os.getenv('EMBEDDING_DIMENSION', 384))
                dim_match = len(embedding) == expected_dim

                self.print_check(
                    "Embedding dimensions",
                    dim_match,
                    f"Generated {len(embedding)}-dimensional embedding (expected: {expected_dim})"
                )

                return True

            except Exception as e:
                self.print_check("Embedding model", False, f"Error loading model: {e}")
                return False

        except ImportError as e:
            self.print_check("Embedding dependencies", False, f"Missing dependencies: {e}")
            return False

    def check_system_resources(self) -> bool:
        """Check system resources."""
        self.print_header("SYSTEM RESOURCES")

        try:
            import shutil

            # Check disk space
            total, used, free = shutil.disk_usage('/')
            free_gb = free / (1024 ** 3)
            total_gb = total / (1024 ** 3)
            used_percent = (used / total) * 100

            self.print_check(
                "Disk space",
                free_gb > 10,
                f"{free_gb:.1f} GB free / {total_gb:.1f} GB total ({used_percent:.1f}% used)",
                warning=(free_gb <= 10)
            )

            # Check logs directory
            log_dir = Path(__file__).parent.parent / 'logs'
            log_dir.mkdir(exist_ok=True)
            self.print_check("Logs directory", log_dir.exists(), f"Directory: {log_dir}")

            # Check data directory
            data_dir = Path(os.getenv('DATA_DIR', './mothra/data'))
            self.print_check(
                "Data directory",
                data_dir.exists() or True,
                f"Directory: {data_dir} (will be created if needed)",
                warning=not data_dir.exists()
            )

            return True

        except Exception as e:
            self.print_check("System resources", False, f"Error: {e}")
            return False

    def check_python_dependencies(self) -> bool:
        """Check Python dependencies."""
        self.print_header("PYTHON DEPENDENCIES")

        required_packages = {
            'sqlalchemy': 'Database ORM',
            'asyncpg': 'PostgreSQL async driver',
            'pgvector': 'pgvector client',
            'sentence_transformers': 'Embedding model',
            'torch': 'PyTorch for embeddings',
            'aiohttp': 'Async HTTP client',
            'pydantic': 'Data validation',
            'dotenv': 'Environment variables'
        }

        all_present = True
        for package, description in required_packages.items():
            try:
                __import__(package)
                self.print_check(f"Package: {package}", True, description)
            except ImportError:
                self.print_check(f"Package: {package}", False, f"{description} - NOT INSTALLED")
                all_present = False

        return all_present

    def print_summary(self):
        """Print summary of all checks."""
        self.print_header("SUMMARY")

        total_checks = self.checks_passed + self.checks_failed
        print(f"Total Checks:     {total_checks}")
        print(f"Passed:           {self.checks_passed} ✓")
        print(f"Failed:           {self.checks_failed} ✗")
        print(f"Warnings:         {self.warnings} ⚠")
        print()

        if self.checks_failed == 0:
            print("✓ System is ready for EPD loading!")
            print("\nTo start loading EPDs, run:")
            print("  python scripts/load_epds_comprehensive.py")
            print("\nOr for a quick test with 100 EPDs:")
            print("  python scripts/load_epds_comprehensive.py --limit 100")
            return True
        else:
            print("✗ System is NOT ready. Please fix the failed checks above.")
            print("\nCommon fixes:")
            print("  1. Start PostgreSQL: docker compose up -d postgres")
            print("  2. Run migrations: alembic upgrade head")
            print("  3. Install dependencies: pip install -r requirements.txt")
            print("  4. Configure .env file with EC3 credentials")
            return False


async def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("MOTHRA EPD VECTOR STORE - SYSTEM READINESS CHECK")
    print("=" * 70)

    verifier = SystemVerifier()

    # Run all checks
    await verifier.check_database()
    await verifier.check_ec3_credentials()
    verifier.check_embedding_model()
    verifier.check_system_resources()
    verifier.check_python_dependencies()

    # Print summary
    ready = verifier.print_summary()

    print("\n" + "=" * 70 + "\n")

    sys.exit(0 if ready else 1)


if __name__ == "__main__":
    asyncio.run(main())
