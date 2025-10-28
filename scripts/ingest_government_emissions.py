#!/usr/bin/env python3
"""
Government Emissions Data Ingestion Script

Downloads and ingests emissions data from top 10 government sources:
1. UK DEFRA 2025 GHG Conversion Factors
2. EPA Supply Chain GHG Emission Factors v1.3 NAICS
3. EPA GHGRP Facility Emissions
4. EPA Emission Factors Hub 2025
5. EU ETS Verified Emissions
6. EEA Emission Factor Database
7. IPCC Emission Factor Database
8. IEA Emissions Factors
9. UK DEFRA 2024 (historical)
10. Climatiq BEIS Data

Usage:
    python scripts/ingest_government_emissions.py --sources all
    python scripts/ingest_government_emissions.py --sources UK_DEFRA_2025,EPA_SUPPLY_CHAIN_V13
    python scripts/ingest_government_emissions.py --priority critical
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

import aiohttp

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mothra.agents.discovery.dataset_discovery import (
    KNOWN_DATASETS,
    DatasetDiscovery,
    FileDownloader,
    DataFileParser,
)
from mothra.agents.parser.parser_registry import ParserRegistry
from mothra.agents.parser.uk_defra_parser import UKDEFRAParser
from mothra.agents.parser.epa_ghgrp_parser import EPAGHGRPParser
from mothra.agents.parser.ipcc_emission_factors_parser import IPCCEmissionFactorParser
from mothra.db.models import DataSource, CarbonEntity
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger
from sqlalchemy import select

logger = get_logger(__name__)


class GovernmentDataIngestion:
    """Orchestrate ingestion from government emissions data sources."""

    def __init__(self):
        self.downloader = None
        self.parser = DataFileParser()
        self.stats = {
            "total_sources": 0,
            "successful_downloads": 0,
            "failed_downloads": 0,
            "total_entities": 0,
            "ingested_entities": 0,
        }

    async def __aenter__(self):
        self.downloader = FileDownloader(
            download_dir=Path("./data/government_emissions")
        )
        await self.downloader.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.downloader:
            await self.downloader.__aexit__(exc_type, exc_val, exc_tb)

    async def ensure_data_source_exists(
        self, dataset_id: str, dataset_info: dict
    ) -> DataSource:
        """
        Ensure a DataSource record exists for this dataset.

        Args:
            dataset_id: Dataset identifier
            dataset_info: Dataset metadata

        Returns:
            DataSource instance
        """
        async with get_db_context() as db:
            # Check if source already exists
            stmt = select(DataSource).where(DataSource.name == dataset_info["name"])
            result = await db.execute(stmt)
            existing_source = result.scalar_one_or_none()

            if existing_source:
                logger.info(
                    "data_source_exists",
                    name=dataset_info["name"],
                    id=existing_source.id,
                )
                return existing_source

            # Create new data source
            source = DataSource(
                name=dataset_info["name"],
                url=dataset_info.get("url", ""),
                source_type=dataset_info.get("source_type", "government_database"),
                data_format=dataset_info.get("format", "unknown"),
                access_method="download",
                status="active",
                priority=dataset_info.get("priority", "medium"),
                metadata={
                    "dataset_id": dataset_id,
                    "description": dataset_info.get("description", ""),
                    "geographic_scope": dataset_info.get("geographic_scope", []),
                    "direct_download": dataset_info.get("direct_download", ""),
                    "file_patterns": dataset_info.get("file_patterns", []),
                },
            )

            db.add(source)
            await db.commit()
            await db.refresh(source)

            logger.info("data_source_created", name=source.name, id=source.id)
            return source

    async def download_epa_supply_chain(self) -> Path | None:
        """
        Download EPA Supply Chain GHG Emission Factors CSV directly.

        Returns:
            Path to downloaded file or None
        """
        dataset = KNOWN_DATASETS["EPA_SUPPLY_CHAIN_V13"]
        url = dataset["direct_download"]

        logger.info("downloading_epa_supply_chain", url=url)

        try:
            filepath = await self.downloader.download_file(url, max_size_mb=50)
            if filepath:
                logger.info("epa_supply_chain_downloaded", path=str(filepath))
                self.stats["successful_downloads"] += 1
                return filepath
            else:
                logger.error("epa_supply_chain_download_failed")
                self.stats["failed_downloads"] += 1
                return None
        except Exception as e:
            logger.error("epa_supply_chain_error", error=str(e))
            self.stats["failed_downloads"] += 1
            return None

    async def scrape_download_links(self, url: str) -> list[str]:
        """
        Scrape download links from a government webpage.

        Args:
            url: Page URL to scrape

        Returns:
            List of download URLs found
        """
        discovery = DatasetDiscovery()
        discovery.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )

        try:
            links = await discovery.extract_download_links(url)
            return links
        except Exception as e:
            logger.error("link_scraping_failed", url=url, error=str(e))
            return []
        finally:
            await discovery.session.close()

    async def ingest_dataset(self, dataset_id: str, dataset_info: dict) -> int:
        """
        Ingest a single dataset.

        Args:
            dataset_id: Dataset identifier
            dataset_info: Dataset metadata

        Returns:
            Number of entities ingested
        """
        logger.info(
            "ingesting_dataset",
            dataset_id=dataset_id,
            name=dataset_info["name"],
            priority=dataset_info.get("priority", "medium"),
        )

        # Ensure data source exists
        data_source = await self.ensure_data_source_exists(dataset_id, dataset_info)

        # Handle direct downloads
        if "direct_download" in dataset_info:
            url = dataset_info["direct_download"]
            logger.info("direct_download_available", url=url)

            filepath = await self.downloader.download_file(url, max_size_mb=200)

            if filepath:
                self.stats["successful_downloads"] += 1
                entities = await self._parse_and_store(
                    filepath, data_source, dataset_info
                )
                return entities
            else:
                self.stats["failed_downloads"] += 1
                return 0

        # Scrape for download links
        page_url = dataset_info.get("url", "")
        if page_url:
            logger.info("scraping_download_links", url=page_url)
            links = await self.scrape_download_links(page_url)

            # Filter links by file patterns
            file_patterns = dataset_info.get("file_patterns", [])
            filtered_links = [
                link
                for link in links
                if any(pattern.lower() in link.lower() for pattern in file_patterns)
            ]

            logger.info(
                "download_links_filtered",
                total=len(links),
                filtered=len(filtered_links),
            )

            # Download and process first matching file
            for link in filtered_links[:3]:  # Limit to first 3 matches
                filepath = await self.downloader.download_file(link, max_size_mb=200)

                if filepath:
                    self.stats["successful_downloads"] += 1
                    entities = await self._parse_and_store(
                        filepath, data_source, dataset_info
                    )
                    if entities > 0:
                        return entities
                else:
                    self.stats["failed_downloads"] += 1

        return 0

    async def _parse_and_store(
        self, filepath: Path, data_source: DataSource, dataset_info: dict
    ) -> int:
        """
        Parse file and store entities.

        Args:
            filepath: Path to downloaded file
            data_source: DataSource instance
            dataset_info: Dataset metadata

        Returns:
            Number of entities stored
        """
        logger.info("parsing_file", file=filepath.name, format=dataset_info["format"])

        # Parse based on format
        entities = []
        try:
            if dataset_info["format"] == "csv" or filepath.suffix.lower() == ".csv":
                entities = await self.parser.parse_csv(filepath, data_source.name)
            elif dataset_info["format"] in ["excel", "xlsx"] or filepath.suffix.lower() in [
                ".xlsx",
                ".xls",
            ]:
                entities = await self.parser.parse_excel(filepath, data_source.name)
            elif dataset_info["format"] == "xml" or filepath.suffix.lower() == ".xml":
                entities = await self.parser.parse_xml(filepath, data_source.name)
            elif filepath.suffix.lower() == ".zip":
                entities = await self.parser.parse_zip(filepath, data_source.name)
            else:
                logger.warning(
                    "unsupported_format",
                    format=dataset_info["format"],
                    file=filepath.name,
                )
                return 0

            self.stats["total_entities"] += len(entities)

            # Store entities in database
            if entities:
                stored = await self._store_entities(entities, data_source)
                self.stats["ingested_entities"] += stored
                logger.info(
                    "entities_ingested",
                    source=data_source.name,
                    total_parsed=len(entities),
                    stored=stored,
                )
                return stored

        except Exception as e:
            logger.error("parse_and_store_error", file=filepath.name, error=str(e))

        return 0

    async def _store_entities(
        self, entity_dicts: list[dict[str, Any]], data_source: DataSource
    ) -> int:
        """
        Store parsed entities in database.

        Args:
            entity_dicts: List of entity dictionaries
            data_source: DataSource instance

        Returns:
            Number of entities stored
        """
        stored_count = 0

        async with get_db_context() as db:
            for entity_dict in entity_dicts:
                try:
                    # Add source_id if not present
                    if "source_id" not in entity_dict:
                        entity_dict["source_id"] = data_source.id

                    # Create CarbonEntity
                    entity = CarbonEntity(**entity_dict)
                    db.add(entity)
                    stored_count += 1

                    # Commit in batches of 100
                    if stored_count % 100 == 0:
                        await db.commit()
                        logger.info("batch_committed", count=stored_count)

                except Exception as e:
                    logger.error(
                        "entity_storage_failed",
                        name=entity_dict.get("name", "unknown"),
                        error=str(e),
                    )

            # Final commit
            await db.commit()

        return stored_count

    async def run_ingestion(
        self, source_ids: list[str] | None = None, priority: str | None = None
    ) -> dict:
        """
        Run ingestion for specified sources.

        Args:
            source_ids: List of dataset IDs to ingest, or None for all
            priority: Priority filter (critical, high, medium, low)

        Returns:
            Statistics dictionary
        """
        # Filter datasets
        datasets_to_ingest = {}

        for dataset_id, dataset_info in KNOWN_DATASETS.items():
            # Filter by source_ids if specified
            if source_ids and dataset_id not in source_ids:
                continue

            # Filter by priority if specified
            if priority and dataset_info.get("priority") != priority:
                continue

            datasets_to_ingest[dataset_id] = dataset_info

        self.stats["total_sources"] = len(datasets_to_ingest)

        logger.info(
            "ingestion_started",
            total_sources=self.stats["total_sources"],
            sources=list(datasets_to_ingest.keys()),
        )

        # Ingest each dataset
        for dataset_id, dataset_info in datasets_to_ingest.items():
            try:
                await self.ingest_dataset(dataset_id, dataset_info)
            except Exception as e:
                logger.error(
                    "dataset_ingestion_failed",
                    dataset_id=dataset_id,
                    error=str(e),
                )
                self.stats["failed_downloads"] += 1

        logger.info("ingestion_complete", stats=self.stats)
        return self.stats


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest emissions data from government sources"
    )
    parser.add_argument(
        "--sources",
        help="Comma-separated list of source IDs, or 'all' for all sources",
        default="all",
    )
    parser.add_argument(
        "--priority",
        choices=["critical", "high", "medium", "low"],
        help="Filter by priority level",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available data sources and exit",
    )

    args = parser.parse_args()

    if args.list:
        print("\nAvailable Government Emissions Data Sources:\n")
        print(f"{'ID':<30} {'Priority':<10} {'Name':<50}")
        print("-" * 90)
        for dataset_id, info in KNOWN_DATASETS.items():
            priority = info.get("priority", "medium")
            name = info["name"]
            print(f"{dataset_id:<30} {priority:<10} {name:<50}")
        print(f"\nTotal: {len(KNOWN_DATASETS)} sources")
        return

    # Parse source list
    source_ids = None
    if args.sources != "all":
        source_ids = [s.strip() for s in args.sources.split(",")]

    # Run ingestion
    async with GovernmentDataIngestion() as ingestion:
        stats = await ingestion.run_ingestion(
            source_ids=source_ids, priority=args.priority
        )

        # Print summary
        print("\n" + "=" * 80)
        print("GOVERNMENT EMISSIONS DATA INGESTION SUMMARY")
        print("=" * 80)
        print(f"Total Sources Processed:  {stats['total_sources']}")
        print(f"Successful Downloads:     {stats['successful_downloads']}")
        print(f"Failed Downloads:         {stats['failed_downloads']}")
        print(f"Total Entities Parsed:    {stats['total_entities']}")
        print(f"Entities Ingested to DB:  {stats['ingested_entities']}")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
