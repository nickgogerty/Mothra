"""
Master Orchestrator: Central coordination for all MOTHRA agents.

Manages workflows:
- daily_update: Incremental updates from active sources
- full_refresh: Complete crawl and reindex
- discover_new: Survey for new sources
- quality_check: Validate and score all data
"""

import asyncio
import time
from datetime import datetime
from typing import Any

from mothra.agents.survey.survey_agent import SurveyAgent
from mothra.agents.crawler.crawler_agent import CrawlerOrchestrator
from mothra.agents.embedding.vector_manager import VectorManager
from mothra.agents.quality.quality_scorer import DataQualityScorer
from mothra.config import settings
from mothra.db.session import init_db
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class MothraOrchestrator:
    """Central orchestration for all Mothra agents."""

    def __init__(self) -> None:
        self.survey_agent = SurveyAgent()
        self.quality_scorer = DataQualityScorer()
        self.vector_manager = VectorManager()

        self.workflows = {
            "daily_update": self.workflow_daily_update,
            "full_refresh": self.workflow_full_refresh,
            "discover_new": self.workflow_discover_new,
            "quality_check": self.workflow_quality_check,
            "reindex_vectors": self.workflow_reindex_vectors,
        }

        self.monitoring = {"metrics": {}, "alerts": [], "logs": []}

    async def execute_workflow(self, workflow_name: str) -> dict[str, Any]:
        """
        Execute a predefined workflow with monitoring.

        Args:
            workflow_name: Name of workflow to execute

        Returns:
            Workflow execution results
        """
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        logger.info("workflow_started", workflow=workflow_name)
        start_time = time.time()

        try:
            workflow_func = self.workflows[workflow_name]
            result = await workflow_func()

            duration = time.time() - start_time

            logger.info(
                "workflow_completed",
                workflow=workflow_name,
                duration_seconds=duration,
                result=result,
            )

            return {
                "workflow": workflow_name,
                "status": "success",
                "duration_seconds": duration,
                "result": result,
            }

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                "workflow_failed", workflow=workflow_name, duration_seconds=duration, error=str(e)
            )

            await self.alert_on_failure(workflow_name, str(e))

            return {
                "workflow": workflow_name,
                "status": "failed",
                "duration_seconds": duration,
                "error": str(e),
            }

    async def workflow_daily_update(self) -> dict[str, Any]:
        """
        Daily update workflow: Incremental crawl of active sources.

        Returns:
            Workflow results
        """
        results = {}

        # Step 1: Crawl critical priority sources
        logger.info("daily_update_step", step=1, action="crawling_critical_sources")

        async with CrawlerOrchestrator() as crawler:
            crawl_stats = await crawler.execute_crawl_plan(priority="critical")
            results["crawl"] = crawl_stats

        # Step 2: Generate embeddings for new entities
        logger.info("daily_update_step", step=2, action="generating_embeddings")

        vector_count = await self.vector_manager.reindex_all()
        results["embeddings"] = {"count": vector_count}

        return results

    async def workflow_full_refresh(self) -> dict[str, Any]:
        """
        Full refresh workflow: Complete crawl and reindex.

        Returns:
            Workflow results
        """
        results = {}

        # Step 1: Crawl all validated sources
        logger.info("full_refresh_step", step=1, action="crawling_all_sources")

        async with CrawlerOrchestrator() as crawler:
            crawl_stats = await crawler.execute_crawl_plan()
            results["crawl"] = crawl_stats

        # Step 2: Quality check all data
        logger.info("full_refresh_step", step=2, action="quality_validation")

        quality_results = await self.workflow_quality_check()
        results["quality"] = quality_results

        # Step 3: Reindex all vectors
        logger.info("full_refresh_step", step=3, action="reindexing_vectors")

        vector_count = await self.vector_manager.reindex_all()
        results["embeddings"] = {"count": vector_count}

        return results

    async def workflow_discover_new(self) -> dict[str, Any]:
        """
        Discover new sources workflow.

        Returns:
            Workflow results
        """
        results = {}

        # Step 1: Run survey agent
        logger.info("discover_new_step", step=1, action="surveying_sources")

        async with self.survey_agent:
            sources_count = await self.survey_agent.discover_sources()
            results["sources_discovered"] = sources_count

        return results

    async def workflow_quality_check(self) -> dict[str, Any]:
        """
        Quality check workflow: Validate and score all data.

        Returns:
            Workflow results
        """
        # This is a simplified version
        # In production, would iterate through all entities

        results = {
            "total_checked": 0,
            "passed": 0,
            "failed": 0,
            "average_score": 0.0,
        }

        logger.info("quality_check_complete", results=results)

        return results

    async def workflow_reindex_vectors(self) -> dict[str, Any]:
        """
        Reindex all vectors workflow.

        Returns:
            Workflow results
        """
        logger.info("reindex_workflow_started")

        count = await self.vector_manager.reindex_all()

        return {"reindexed_count": count}

    async def alert_on_failure(self, workflow: str, error: str) -> None:
        """
        Send alert on workflow failure.

        Args:
            workflow: Workflow name
            error: Error message
        """
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow": workflow,
            "error": error,
            "severity": "error",
        }

        self.monitoring["alerts"].append(alert)

        logger.error("workflow_alert", alert=alert)

    async def run_scheduled_workflows(self) -> None:
        """
        Run workflows on schedule (would use APScheduler in production).
        """
        while True:
            try:
                # Daily update at 2 AM
                await self.execute_workflow("daily_update")

                # Sleep for 24 hours
                await asyncio.sleep(86400)

            except Exception as e:
                logger.error("scheduler_error", error=str(e))
                await asyncio.sleep(3600)  # Retry in 1 hour


async def main() -> None:
    """CLI entry point for orchestrator."""
    logger.info("mothra_orchestrator_starting")

    # Initialize database
    await init_db()
    logger.info("database_initialized")

    orchestrator = MothraOrchestrator()

    # Run discovery workflow
    result = await orchestrator.execute_workflow("discover_new")
    logger.info("discovery_complete", result=result)

    # Run daily update
    result = await orchestrator.execute_workflow("daily_update")
    logger.info("daily_update_complete", result=result)


if __name__ == "__main__":
    asyncio.run(main())
