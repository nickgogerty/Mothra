#!/usr/bin/env python3
"""
EIA (Energy Information Administration) Data Ingestion Script

Fetches energy and emissions data from EIA's Open Data API v2.
This script targets high-volume endpoints to quickly populate the database with 15K+ records:
1. Facility Fuel Data - Power plant emissions and fuel consumption (15,000+ facilities)
2. CO2 Emissions Aggregates - State-level emissions by sector and fuel (multi-year)
3. Electricity Generation - State and regional generation data

Prerequisites:
- EIA API key (free from https://www.eia.gov/opendata/)
- Set EIA_API_KEY environment variable or add to .env file

Usage:
    # Ingest all high-volume data (facility + state emissions)
    python scripts/ingest_eia_data.py --all

    # Ingest only facility data
    python scripts/ingest_eia_data.py --facility

    # Ingest only state CO2 emissions
    python scripts/ingest_eia_data.py --emissions

    # Limit records per endpoint
    python scripts/ingest_eia_data.py --all --max-records 5000

    # Test with small dataset
    python scripts/ingest_eia_data.py --all --max-records 100
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mothra.agents.discovery.eia_integration import EIAClient
from mothra.agents.parser.eia_parser import EIAParser
from mothra.db.models import DataSource, CarbonEntity, CrawlLog
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger
from sqlalchemy import select

logger = get_logger(__name__)


class EIADataIngestion:
    """Orchestrate ingestion from EIA API."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize EIA ingestion.

        Args:
            api_key: EIA API key (optional, will try to load from environment)
        """
        self.api_key = api_key
        self.client = None
        self.stats = {
            "facility_records": 0,
            "emissions_records": 0,
            "total_entities_created": 0,
            "total_entities_failed": 0,
            "start_time": None,
            "end_time": None,
        }

    async def ensure_data_source_exists(self, source_name: str, source_info: dict) -> DataSource:
        """
        Ensure a DataSource record exists for EIA endpoint.

        Args:
            source_name: Name of the data source
            source_info: Metadata about the source

        Returns:
            DataSource instance
        """
        async with get_db_context() as db:
            # Check if source already exists
            stmt = select(DataSource).where(DataSource.name == source_name)
            result = await db.execute(stmt)
            existing_source = result.scalar_one_or_none()

            if existing_source:
                logger.info(
                    "data_source_exists",
                    name=source_name,
                    id=existing_source.id,
                )
                return existing_source

            # Create new data source
            source = DataSource(
                name=source_name,
                url=source_info.get("url", "https://api.eia.gov/v2/"),
                source_type="api",
                category="government",
                data_format="json",
                access_method="rest",
                auth_required=True,
                status="active",
                priority=source_info.get("priority", "high"),
                rate_limit=100,  # EIA rate limit
                extra_metadata={
                    "description": source_info.get("description", ""),
                    "geographic_scope": ["USA"],
                    "api_version": "v2",
                    "endpoint": source_info.get("endpoint", ""),
                },
            )

            db.add(source)
            await db.commit()
            await db.refresh(source)

            logger.info("data_source_created", name=source.name, id=source.id)
            return source

    async def ingest_facility_data(
        self,
        max_records: int | None = None,
        state_ids: list[str] | None = None,
    ) -> int:
        """
        Ingest facility fuel consumption and emissions data.

        Args:
            max_records: Maximum number of records to fetch
            state_ids: List of state codes to filter by

        Returns:
            Number of entities created
        """
        logger.info(
            "ingestion_start",
            endpoint="facility_fuel",
            max_records=max_records,
            states=state_ids or "all",
        )

        # Ensure data source exists
        source = await self.ensure_data_source_exists(
            "EIA Facility Data",
            {
                "url": "https://api.eia.gov/v2/electricity/facility-fuel/data",
                "description": "Power plant facility fuel consumption and emissions data",
                "priority": "high",
                "endpoint": "electricity/facility-fuel",
            },
        )

        # Create parser
        parser = EIAParser(source)

        # Create crawl log
        crawl_log = await self._create_crawl_log(source.id, "facility_fuel")

        try:
            # Fetch data from API
            async with EIAClient(api_key=self.api_key) as client:
                records = await client.get_facility_fuel_data(
                    state_ids=state_ids,
                    frequency="annual",
                    max_records=max_records,
                )

            logger.info(
                "data_fetched",
                endpoint="facility_fuel",
                record_count=len(records),
            )

            self.stats["facility_records"] = len(records)

            # Parse records
            entities = await parser.parse(records)

            # Store entities in database
            entities_created = await self._store_entities(entities, source.id)

            # Update crawl log
            await self._update_crawl_log(
                crawl_log.id,
                status="completed",
                records_found=len(records),
                records_processed=len(entities),
                records_inserted=entities_created,
            )

            logger.info(
                "ingestion_complete",
                endpoint="facility_fuel",
                records=len(records),
                entities_created=entities_created,
            )

            return entities_created

        except Exception as e:
            logger.error(
                "ingestion_failed",
                endpoint="facility_fuel",
                error=str(e),
                exception_type=type(e).__name__,
            )

            # Update crawl log with error
            await self._update_crawl_log(
                crawl_log.id,
                status="failed",
                error_message=str(e),
            )

            return 0

    async def ingest_co2_emissions(
        self,
        max_records: int | None = None,
        state_ids: list[str] | None = None,
    ) -> int:
        """
        Ingest state-level CO2 emissions aggregates.

        Args:
            max_records: Maximum number of records to fetch
            state_ids: List of state codes to filter by

        Returns:
            Number of entities created
        """
        logger.info(
            "ingestion_start",
            endpoint="co2_emissions",
            max_records=max_records,
            states=state_ids or "all",
        )

        # Ensure data source exists
        source = await self.ensure_data_source_exists(
            "EIA CO2 Emissions",
            {
                "url": "https://api.eia.gov/v2/co2-emissions/co2-emissions-aggregates/data",
                "description": "State-level CO2 emissions by sector and fuel type",
                "priority": "high",
                "endpoint": "co2-emissions/co2-emissions-aggregates",
            },
        )

        # Create parser
        parser = EIAParser(source)

        # Create crawl log
        crawl_log = await self._create_crawl_log(source.id, "co2_emissions")

        try:
            # Fetch data from API
            async with EIAClient(api_key=self.api_key) as client:
                records = await client.get_co2_emissions_aggregates(
                    state_ids=state_ids,
                    max_records=max_records,
                )

            logger.info(
                "data_fetched",
                endpoint="co2_emissions",
                record_count=len(records),
            )

            self.stats["emissions_records"] = len(records)

            # Parse records
            entities = await parser.parse(records)

            # Store entities in database
            entities_created = await self._store_entities(entities, source.id)

            # Update crawl log
            await self._update_crawl_log(
                crawl_log.id,
                status="completed",
                records_found=len(records),
                records_processed=len(entities),
                records_inserted=entities_created,
            )

            logger.info(
                "ingestion_complete",
                endpoint="co2_emissions",
                records=len(records),
                entities_created=entities_created,
            )

            return entities_created

        except Exception as e:
            logger.error(
                "ingestion_failed",
                endpoint="co2_emissions",
                error=str(e),
                exception_type=type(e).__name__,
            )

            # Update crawl log with error
            await self._update_crawl_log(
                crawl_log.id,
                status="failed",
                error_message=str(e),
            )

            return 0

    async def ingest_all(
        self,
        max_records_per_endpoint: int | None = None,
        state_ids: list[str] | None = None,
    ) -> dict[str, int]:
        """
        Ingest data from all major EIA endpoints.

        Args:
            max_records_per_endpoint: Maximum records per endpoint
            state_ids: List of state codes to filter by

        Returns:
            Dict with counts per endpoint
        """
        self.stats["start_time"] = datetime.now()

        logger.info(
            "eia_ingestion_start",
            max_records_per_endpoint=max_records_per_endpoint,
            states=state_ids or "all",
        )

        results = {}

        # Ingest facility data
        try:
            facility_count = await self.ingest_facility_data(
                max_records=max_records_per_endpoint,
                state_ids=state_ids,
            )
            results["facility_data"] = facility_count
            self.stats["total_entities_created"] += facility_count
        except Exception as e:
            logger.error("facility_ingestion_failed", error=str(e))
            results["facility_data"] = 0

        # Ingest CO2 emissions
        try:
            emissions_count = await self.ingest_co2_emissions(
                max_records=max_records_per_endpoint,
                state_ids=state_ids,
            )
            results["co2_emissions"] = emissions_count
            self.stats["total_entities_created"] += emissions_count
        except Exception as e:
            logger.error("emissions_ingestion_failed", error=str(e))
            results["co2_emissions"] = 0

        self.stats["end_time"] = datetime.now()
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()

        logger.info(
            "eia_ingestion_complete",
            total_entities=self.stats["total_entities_created"],
            duration_seconds=duration,
            results=results,
        )

        return results

    async def _create_crawl_log(self, source_id: int, endpoint: str) -> CrawlLog:
        """Create a crawl log entry."""
        async with get_db_context() as db:
            crawl_log = CrawlLog(
                source_id=source_id,
                status="running",
                extra_metadata={"endpoint": endpoint},
            )
            db.add(crawl_log)
            await db.commit()
            await db.refresh(crawl_log)
            return crawl_log

    async def _update_crawl_log(
        self,
        crawl_log_id: int,
        status: str,
        records_found: int = 0,
        records_processed: int = 0,
        records_inserted: int = 0,
        error_message: str | None = None,
    ):
        """Update crawl log with results."""
        async with get_db_context() as db:
            stmt = select(CrawlLog).where(CrawlLog.id == crawl_log_id)
            result = await db.execute(stmt)
            crawl_log = result.scalar_one_or_none()

            if crawl_log:
                crawl_log.status = status
                crawl_log.records_found = records_found
                crawl_log.records_processed = records_processed
                crawl_log.records_inserted = records_inserted
                if error_message:
                    crawl_log.error_message = error_message
                await db.commit()

    async def _store_entities(self, entities: list[dict[str, Any]], source_id: int) -> int:
        """
        Store parsed entities in the database.

        Args:
            entities: List of entity dictionaries
            source_id: DataSource ID

        Returns:
            Number of entities successfully stored
        """
        if not entities:
            return 0

        stored_count = 0
        failed_count = 0

        async with get_db_context() as db:
            for entity_dict in entities:
                try:
                    # Remove 'id' if present (will be auto-generated)
                    entity_dict.pop("id", None)

                    # Ensure source_id is set
                    entity_dict["source_uuid"] = source_id

                    # Create entity
                    entity = CarbonEntity(**entity_dict)
                    db.add(entity)

                    stored_count += 1

                    # Commit in batches of 100
                    if stored_count % 100 == 0:
                        await db.commit()
                        logger.info(
                            "batch_committed",
                            stored_count=stored_count,
                        )

                except Exception as e:
                    failed_count += 1
                    logger.error(
                        "entity_storage_failed",
                        entity_name=entity_dict.get("name", "unknown"),
                        error=str(e),
                    )
                    continue

            # Final commit
            try:
                await db.commit()
            except Exception as e:
                logger.error("final_commit_failed", error=str(e))
                await db.rollback()

        self.stats["total_entities_failed"] += failed_count

        logger.info(
            "entities_stored",
            stored=stored_count,
            failed=failed_count,
        )

        return stored_count


async def main():
    """Main ingestion function."""
    parser = argparse.ArgumentParser(
        description="Ingest EIA energy and emissions data"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ingest all high-volume endpoints",
    )
    parser.add_argument(
        "--facility",
        action="store_true",
        help="Ingest facility fuel data only",
    )
    parser.add_argument(
        "--emissions",
        action="store_true",
        help="Ingest CO2 emissions aggregates only",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Maximum records per endpoint (default: unlimited)",
    )
    parser.add_argument(
        "--states",
        type=str,
        default=None,
        help="Comma-separated state codes (e.g., CA,NY,TX)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="EIA API key (or set EIA_API_KEY environment variable)",
    )

    args = parser.parse_args()

    # Parse state codes
    state_ids = None
    if args.states:
        state_ids = [s.strip().upper() for s in args.states.split(",")]

    # Create ingestion instance
    ingestion = EIADataIngestion(api_key=args.api_key)

    try:
        if args.all or (not args.facility and not args.emissions):
            # Ingest all endpoints
            results = await ingestion.ingest_all(
                max_records_per_endpoint=args.max_records,
                state_ids=state_ids,
            )
            print("\n=== EIA Ingestion Complete ===")
            print(f"Facility data: {results.get('facility_data', 0)} entities")
            print(f"CO2 emissions: {results.get('co2_emissions', 0)} entities")
            print(f"Total: {sum(results.values())} entities")

        elif args.facility:
            # Ingest facility data only
            count = await ingestion.ingest_facility_data(
                max_records=args.max_records,
                state_ids=state_ids,
            )
            print(f"\n=== Facility Data Ingestion Complete ===")
            print(f"Created {count} entities")

        elif args.emissions:
            # Ingest emissions data only
            count = await ingestion.ingest_co2_emissions(
                max_records=args.max_records,
                state_ids=state_ids,
            )
            print(f"\n=== CO2 Emissions Ingestion Complete ===")
            print(f"Created {count} entities")

        # Print final stats
        print(f"\n=== Statistics ===")
        print(f"Facility records fetched: {ingestion.stats['facility_records']}")
        print(f"Emissions records fetched: {ingestion.stats['emissions_records']}")
        print(f"Total entities created: {ingestion.stats['total_entities_created']}")
        print(f"Total entities failed: {ingestion.stats['total_entities_failed']}")

        if ingestion.stats["start_time"] and ingestion.stats["end_time"]:
            duration = (ingestion.stats["end_time"] - ingestion.stats["start_time"]).total_seconds()
            print(f"Duration: {duration:.2f} seconds")

    except Exception as e:
        logger.error("main_ingestion_failed", error=str(e))
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
