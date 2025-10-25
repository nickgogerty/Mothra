"""
Crawler Orchestrator: Manages distributed crawling across multiple sources.

This agent handles:
- Priority-based crawling queue
- Rate limiting per source
- Retry logic with exponential backoff
- Multiple collection methods (API, web scraping, document extraction)
- Progress tracking and logging
"""

import asyncio
from datetime import datetime
from typing import Any
from uuid import UUID

import aiohttp
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from mothra.config import settings
from mothra.db.models import CarbonEntity, CrawlLog, DataSource
from mothra.db.session import get_db_context
from mothra.agents.parser.parser_registry import ParserRegistry
from mothra.utils.logging import get_logger
from mothra.utils.rate_limiter import AdaptiveRateLimiter
from mothra.utils.retry import async_retry

logger = get_logger(__name__)


class CrawlerOrchestrator:
    """Orchestrates crawling across multiple data sources."""

    def __init__(self) -> None:
        self.crawl_queue: asyncio.Queue[DataSource] = asyncio.Queue()
        self.rate_limiters: dict[str, AdaptiveRateLimiter] = {}
        self.session: aiohttp.ClientSession | None = None
        self.max_concurrent = settings.max_concurrent_requests

    async def __aenter__(self) -> "CrawlerOrchestrator":
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.request_timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def get_rate_limiter(self, source: DataSource) -> AdaptiveRateLimiter:
        """
        Get or create a rate limiter for a source.

        Args:
            source: Data source

        Returns:
            AdaptiveRateLimiter instance
        """
        source_key = str(source.id)

        if source_key not in self.rate_limiters:
            rate_limit = source.rate_limit or settings.default_rate_limit
            self.rate_limiters[source_key] = AdaptiveRateLimiter(
                calls=rate_limit, period=60, min_calls=1
            )

        return self.rate_limiters[source_key]

    async def populate_queue(self, priority: str | None = None) -> int:
        """
        Populate crawl queue with sources.

        Args:
            priority: Optional priority filter (critical, high, medium, low)

        Returns:
            Number of sources added to queue
        """
        async with get_db_context() as db:
            stmt = select(DataSource).where(DataSource.status.in_(["validated", "active"]))

            if priority:
                stmt = stmt.where(DataSource.priority == priority)

            # Order by priority and last crawled
            stmt = stmt.order_by(
                DataSource.priority.desc(), DataSource.last_crawled.asc().nullsfirst()
            )

            result = await db.execute(stmt)
            sources = result.scalars().all()

            count = 0
            for source in sources:
                await self.crawl_queue.put(source)
                count += 1

        logger.info("crawl_queue_populated", count=count, priority=priority)
        return count

    @async_retry(retry_exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def crawl_api(self, source: DataSource) -> dict[str, Any]:
        """
        Crawl an API source.

        Args:
            source: Data source with API configuration

        Returns:
            Dictionary with crawl results
        """
        if not self.session:
            raise RuntimeError("Session not initialized")

        rate_limiter = self.get_rate_limiter(source)

        async with rate_limiter:
            headers = {}
            if source.auth_required and source.metadata.get("api_key"):
                headers["Authorization"] = f"Bearer {source.metadata['api_key']}"

            async with self.session.get(source.url, headers=headers) as response:
                if response.status == 429:  # Too Many Requests
                    rate_limiter.decrease_rate()
                    raise aiohttp.ClientError("Rate limit exceeded")

                response.raise_for_status()

                if source.data_format == "json":
                    data = await response.json()
                elif source.data_format == "xml":
                    data = await response.text()
                else:
                    data = await response.read()

                return {
                    "status": "success",
                    "data": data,
                    "http_status": response.status,
                    "content_length": len(str(data)),
                }

    async def crawl_website(self, source: DataSource) -> dict[str, Any]:
        """
        Scrape a website source.

        Args:
            source: Data source to scrape

        Returns:
            Dictionary with crawl results
        """
        if not self.session:
            raise RuntimeError("Session not initialized")

        rate_limiter = self.get_rate_limiter(source)

        async with rate_limiter:
            async with self.session.get(source.url) as response:
                response.raise_for_status()
                html = await response.text()

                return {
                    "status": "success",
                    "data": html,
                    "http_status": response.status,
                    "content_length": len(html),
                }

    async def process_source(self, source: DataSource) -> None:
        """
        Process a single data source: crawl, parse, and store.

        Args:
            source: Data source to process
        """
        log_entry = CrawlLog(
            source_id=source.id,
            started_at=datetime.utcnow(),
            status="running",
            records_found=0,
            records_processed=0,
        )

        try:
            logger.info(
                "crawl_started",
                source_name=source.name,
                source_type=source.source_type,
                access_method=source.access_method,
            )

            # Route to appropriate crawler based on access method
            if source.access_method in ["rest", "api"]:
                result = await self.crawl_api(source)
            elif source.access_method == "scrape":
                result = await self.crawl_website(source)
            else:
                logger.warning("unsupported_access_method", method=source.access_method)
                result = {"status": "skipped", "reason": "unsupported_access_method"}

            # Parse data if crawl was successful
            entities_stored = 0
            if result.get("status") == "success" and "data" in result:
                raw_data = result["data"]

                # Get appropriate parser from registry
                parser = ParserRegistry.get_parser(source)

                if parser:
                    logger.info(
                        "parsing_started",
                        source_name=source.name,
                        parser=parser.__class__.__name__,
                    )

                    # Parse and validate data
                    entity_dicts = await parser.parse_and_validate(raw_data)
                    log_entry.records_found = len(entity_dicts)

                    # Store entities in database
                    if entity_dicts:
                        entities_stored = await self._store_entities(entity_dicts)
                        log_entry.records_processed = entities_stored

                        logger.info(
                            "entities_stored",
                            source_name=source.name,
                            total=len(entity_dicts),
                            stored=entities_stored,
                        )
                else:
                    logger.warning(
                        "no_parser_available",
                        source_name=source.name,
                    )

            # Update log entry
            log_entry.completed_at = datetime.utcnow()
            log_entry.status = result.get("status", "completed")
            log_entry.duration_seconds = (
                log_entry.completed_at - log_entry.started_at
            ).total_seconds()

            logger.info(
                "crawl_completed",
                source_name=source.name,
                status=log_entry.status,
                duration=log_entry.duration_seconds,
                entities_stored=entities_stored,
            )

            # Update source
            async with get_db_context() as db:
                stmt = (
                    update(DataSource)
                    .where(DataSource.id == source.id)
                    .values(
                        last_crawled=datetime.utcnow(),
                        last_successful_crawl=datetime.utcnow(),
                        status="active",
                    )
                )
                await db.execute(stmt)
                db.add(log_entry)
                await db.commit()

        except Exception as e:
            logger.error("crawl_failed", source_name=source.name, error=str(e))

            log_entry.completed_at = datetime.utcnow()
            log_entry.status = "failed"
            log_entry.error_message = str(e)
            log_entry.duration_seconds = (
                log_entry.completed_at - log_entry.started_at
            ).total_seconds()

            # Update source error count
            async with get_db_context() as db:
                stmt = (
                    update(DataSource)
                    .where(DataSource.id == source.id)
                    .values(
                        last_crawled=datetime.utcnow(),
                        error_count=DataSource.error_count + 1,
                        status="failed" if source.error_count >= 3 else "active",
                    )
                )
                await db.execute(stmt)
                db.add(log_entry)
                await db.commit()

    async def _store_entities(self, entity_dicts: list[dict[str, Any]]) -> int:
        """
        Store parsed entities in the database.

        Args:
            entity_dicts: List of entity dictionaries from parser

        Returns:
            Number of entities successfully stored
        """
        stored_count = 0

        async with get_db_context() as db:
            for entity_dict in entity_dicts:
                try:
                    # Create CarbonEntity from dict
                    entity = CarbonEntity(**entity_dict)
                    db.add(entity)
                    stored_count += 1
                except Exception as e:
                    logger.error(
                        "entity_storage_failed",
                        entity_name=entity_dict.get("name", "unknown"),
                        error=str(e),
                    )

            # Commit all entities
            await db.commit()

        return stored_count

    async def execute_crawl_plan(self, priority: str | None = None) -> dict[str, int]:
        """
        Main orchestration loop - execute crawling plan.

        Args:
            priority: Optional priority filter

        Returns:
            Dictionary with crawl statistics
        """
        stats = {
            "total_sources": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
        }

        # Populate queue
        stats["total_sources"] = await self.populate_queue(priority)

        # Create worker tasks
        workers = [
            asyncio.create_task(self.worker(f"worker-{i}"))
            for i in range(self.max_concurrent)
        ]

        # Wait for queue to be processed
        await self.crawl_queue.join()

        # Cancel workers
        for worker in workers:
            worker.cancel()

        await asyncio.gather(*workers, return_exceptions=True)

        logger.info("crawl_plan_complete", stats=stats)
        return stats

    async def worker(self, name: str) -> None:
        """
        Worker coroutine for processing crawl queue.

        Args:
            name: Worker name for logging
        """
        while True:
            try:
                source = await self.crawl_queue.get()
                logger.debug("worker_processing", worker=name, source=source.name)
                await self.process_source(source)
                self.crawl_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("worker_error", worker=name, error=str(e))
                self.crawl_queue.task_done()


async def main() -> None:
    """CLI entry point for running crawler."""
    logger.info("crawler_orchestrator_starting")

    async with CrawlerOrchestrator() as crawler:
        stats = await crawler.execute_crawl_plan(priority="critical")
        logger.info("crawler_orchestrator_complete", stats=stats)


if __name__ == "__main__":
    asyncio.run(main())
