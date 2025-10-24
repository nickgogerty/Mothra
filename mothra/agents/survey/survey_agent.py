"""
Survey Agent: Discovers and catalogs carbon data sources.

This agent is responsible for:
- Loading initial source catalog
- Discovering new sources through web search and link analysis
- Validating source accessibility
- Extracting metadata
- Populating the data_sources table
"""

import asyncio
from pathlib import Path
from typing import Any
from uuid import UUID

import aiohttp
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mothra.config import settings
from mothra.db.models import DataSource
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger
from mothra.utils.retry import async_retry

logger = get_logger(__name__)


class SurveyAgent:
    """Agent for discovering and validating carbon data sources."""

    def __init__(self) -> None:
        self.catalog_path = Path("mothra/data/sources_catalog.yaml")
        self.session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "SurveyAgent":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.request_timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def load_catalog(self) -> dict[str, Any]:
        """
        Load the initial sources catalog from YAML.

        Returns:
            Dictionary of source categories and their sources
        """
        try:
            with open(self.catalog_path) as f:
                catalog = yaml.safe_load(f)
            logger.info("catalog_loaded", path=str(self.catalog_path))
            return catalog
        except Exception as e:
            logger.error("catalog_load_failed", path=str(self.catalog_path), error=str(e))
            raise

    async def validate_source(self, source_data: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """
        Validate a data source's accessibility and extract metadata.

        Args:
            source_data: Source configuration dictionary

        Returns:
            Tuple of (is_valid, metadata_dict)
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        metadata: dict[str, Any] = {
            "validation_timestamp": None,
            "response_time_ms": None,
            "http_status": None,
            "content_type": None,
            "has_api_docs": False,
            "requires_auth": source_data.get("auth_required", False),
        }

        try:
            url = source_data.get("url", "")
            if not url:
                return False, metadata

            start_time = asyncio.get_event_loop().time()

            async with self.session.head(url, allow_redirects=True) as response:
                end_time = asyncio.get_event_loop().time()

                metadata["http_status"] = response.status
                metadata["response_time_ms"] = (end_time - start_time) * 1000
                metadata["content_type"] = response.headers.get("Content-Type", "")

                # Consider 2xx and 3xx as valid
                is_valid = 200 <= response.status < 400

                logger.info(
                    "source_validated",
                    url=url,
                    status=response.status,
                    valid=is_valid,
                    response_time=metadata["response_time_ms"],
                )

                return is_valid, metadata

        except Exception as e:
            logger.warning("source_validation_failed", url=source_data.get("url"), error=str(e))
            return False, metadata

    async def discover_sources(self) -> int:
        """
        Main discovery workflow: Load catalog and populate database.

        Returns:
            Number of sources added to database
        """
        catalog = await self.load_catalog()
        sources_added = 0

        async with get_db_context() as db:
            # Process all source categories
            for category_name, sources in catalog.items():
                if not isinstance(sources, list):
                    continue

                logger.info("processing_category", category=category_name, count=len(sources))

                for source_data in sources:
                    try:
                        # Check if source already exists
                        name = source_data.get("name", "")
                        if not name:
                            continue

                        stmt = select(DataSource).where(DataSource.name == name)
                        result = await db.execute(stmt)
                        existing = result.scalar_one_or_none()

                        if existing:
                            logger.debug("source_exists", name=name)
                            continue

                        # Validate source
                        is_valid, validation_metadata = await self.validate_source(source_data)

                        # Create data source record
                        data_source = DataSource(
                            name=name,
                            url=source_data.get("url", ""),
                            source_type=source_data.get("source_type", "unknown"),
                            category=source_data.get("category", "unknown"),
                            priority=source_data.get("priority", "medium"),
                            access_method=source_data.get("access_method", "scrape"),
                            auth_required=source_data.get("auth_required", False),
                            rate_limit=source_data.get("rate_limit"),
                            update_frequency=source_data.get("update_frequency"),
                            data_format=source_data.get("data_format"),
                            estimated_size_gb=source_data.get("estimated_size_gb"),
                            schema_type=source_data.get("schema_type"),
                            status="validated" if is_valid else "discovered",
                            error_count=0 if is_valid else 1,
                            metadata={
                                **validation_metadata,
                                "regions": source_data.get("regions", []),
                                "focus": source_data.get("focus"),
                                "license_required": source_data.get("license_required", False),
                            },
                        )

                        db.add(data_source)
                        sources_added += 1

                        logger.info(
                            "source_added",
                            name=name,
                            category=category_name,
                            status=data_source.status,
                        )

                    except Exception as e:
                        logger.error(
                            "source_processing_failed",
                            name=source_data.get("name", "unknown"),
                            error=str(e),
                        )
                        continue

            await db.commit()

        logger.info("discovery_complete", sources_added=sources_added)
        return sources_added

    async def get_sources_by_priority(
        self, priority: str, limit: int = 10
    ) -> list[DataSource]:
        """
        Get sources by priority level.

        Args:
            priority: Priority level (critical, high, medium, low)
            limit: Maximum number of sources to return

        Returns:
            List of DataSource objects
        """
        async with get_db_context() as db:
            stmt = (
                select(DataSource)
                .where(DataSource.priority == priority)
                .where(DataSource.status == "validated")
                .limit(limit)
            )
            result = await db.execute(stmt)
            return list(result.scalars().all())

    async def update_source_status(
        self, source_id: UUID, status: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Update source status and metadata.

        Args:
            source_id: Source UUID
            status: New status
            metadata: Optional metadata to merge
        """
        async with get_db_context() as db:
            stmt = select(DataSource).where(DataSource.id == source_id)
            result = await db.execute(stmt)
            source = result.scalar_one_or_none()

            if source:
                source.status = status
                if metadata:
                    source.metadata = {**source.metadata, **metadata}
                await db.commit()
                logger.info("source_status_updated", source_id=str(source_id), status=status)


async def main() -> None:
    """CLI entry point for running survey agent."""
    logger.info("survey_agent_starting")

    async with SurveyAgent() as agent:
        sources_count = await agent.discover_sources()
        logger.info("survey_agent_complete", sources_discovered=sources_count)


if __name__ == "__main__":
    asyncio.run(main())
