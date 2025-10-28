#!/usr/bin/env python3
"""
Query critical priority data sources from the Mothra database.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from mothra.db.session import get_db_context
from mothra.db.models import DataSource


async def query_critical_sources():
    """Query and display critical priority data sources."""
    async with get_db_context() as session:
        # Check if data_sources table exists
        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'data_sources'
                );
            """)
        )
        table_exists = result.scalar()

        if not table_exists:
            print("⚠️  data_sources table does not exist yet.")
            print("Run database initialization first:")
            print("  python -m mothra.db.session")
            return

        # Query critical priority sources
        stmt = select(DataSource).where(DataSource.priority == "critical")
        result = await session.execute(stmt)
        sources = result.scalars().all()

        if not sources:
            print("No critical priority data sources found in database.")
            print("\nSources may need to be loaded from sources_catalog.yaml")
            return

        print(f"\n{'='*80}")
        print(f"CRITICAL PRIORITY DATA SOURCES ({len(sources)} total)")
        print(f"{'='*80}\n")

        for i, source in enumerate(sources, 1):
            print(f"{i}. {source.name}")
            print(f"   Category: {source.category}")
            print(f"   URL: {source.url}")
            print(f"   Status: {source.status}")
            print(f"   Priority: {source.priority}")
            if source.access_method:
                print(f"   Access Method: {source.access_method}")
            if source.data_format:
                print(f"   Format: {source.data_format}")
            print()


async def main():
    """Main entry point."""
    try:
        await query_critical_sources()
    except Exception as e:
        print(f"Error querying database: {e}")
        print("\nMake sure PostgreSQL is running:")
        print("  docker-compose up -d postgres")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
