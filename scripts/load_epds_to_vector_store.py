#!/usr/bin/env python3
"""
EPD Vector Store Loader
=======================
Extracts all EPDs from EC3 API, tokenizes, chunks, and loads into vector store.

This script:
1. Fetches all EPD records from EC3 API with pagination
2. Parses EPDs into CarbonEntity and CarbonEntityVerification records
3. Chunks large EPD text into manageable pieces
4. Generates embeddings and stores in PostgreSQL with pgvector
5. Creates searchable vector index for semantic search

Usage:
    python scripts/load_epds_to_vector_store.py [--limit N] [--batch-size N] [--skip-existing]
"""

import asyncio
import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mothra.agents.discovery.ec3_integration import EC3Client, EC3EPDParser
from mothra.agents.embedding.vector_manager import VectorManager
from mothra.utils.text_chunker import TextChunker, create_searchable_text_for_chunking
from mothra.db.session import AsyncSessionLocal
from mothra.db.models import CarbonEntity, EmissionFactor, DataSource
from mothra.db.models_verification import CarbonEntityVerification
from mothra.db.models_chunks import DocumentChunk
from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'epd_vectorization_{datetime.now():%Y%m%d_%H%M%S}.log')
    ]
)
logger = logging.getLogger(__name__)


class EPDVectorLoader:
    """Loads EPD data from EC3 into vector store with chunking and embeddings."""

    def __init__(
        self,
        ec3_client: EC3Client,
        vector_manager: VectorManager,
        text_chunker: TextChunker,
        batch_size: int = 50,
        skip_existing: bool = False
    ):
        self.ec3_client = ec3_client
        self.vector_manager = vector_manager
        self.text_chunker = text_chunker
        self.batch_size = batch_size
        self.skip_existing = skip_existing

        self.stats = {
            'total_fetched': 0,
            'total_processed': 0,
            'total_inserted': 0,
            'total_updated': 0,
            'total_embedded': 0,
            'total_chunks': 0,
            'total_skipped': 0,
            'total_errors': 0,
            'start_time': datetime.now(UTC)
        }

    async def get_or_create_data_source(self, session) -> DataSource:
        """Get or create EC3 data source record."""
        result = await session.execute(
            select(DataSource).where(DataSource.name == "EC3 (Building Transparency)")
        )
        source = result.scalar_one_or_none()

        if not source:
            source = DataSource(
                name="EC3 (Building Transparency)",
                url="https://buildingtransparency.org",
                source_type="api",
                category="epd_database",
                access_method="rest_api",
                auth_required=True,
                rate_limit=100,
                update_frequency="daily",
                data_format="json",
                estimated_size_gb=5.0,
                status="active",
                extra_metadata={
                    "description": "EC3 - Embodied Carbon in Construction Calculator",
                    "records_count": "90000+",
                    "coverage": "global"
                }
            )
            session.add(source)
            await session.commit()
            await session.refresh(source)
            logger.info(f"Created data source: {source.name} (ID: {source.id})")

        return source

    async def fetch_all_epds(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all EPDs from EC3 API with pagination."""
        logger.info("Starting EPD extraction from EC3 API...")

        try:
            # Use EC3Client as context manager to ensure session is initialized
            async with self.ec3_client as client:
                # Validate credentials first
                is_valid = await client.validate_credentials()
                if not is_valid:
                    raise ValueError("EC3 API credentials are invalid. Check your API key or OAuth credentials.")

                logger.info("EC3 credentials validated successfully")

                # Fetch all EPDs with pagination
                all_epds = []
                offset = 0
                batch_size = 100  # Results per request

                while True:
                    logger.info(f"Fetching EPDs at offset {offset}...")

                    # Use search_epds with offset-based pagination
                    response = await client.search_epds(
                        limit=batch_size,
                        offset=offset
                    )

                    if not response or 'results' not in response:
                        logger.warning(f"No results in response at offset {offset}")
                        break

                    epds = response['results']
                    if not epds:
                        logger.info("No more EPDs to fetch")
                        break

                    all_epds.extend(epds)
                    self.stats['total_fetched'] = len(all_epds)

                    logger.info(f"Fetched {len(epds)} EPDs (total: {len(all_epds)})")

                    # Check if we've hit the limit
                    if limit and len(all_epds) >= limit:
                        all_epds = all_epds[:limit]
                        logger.info(f"Reached limit of {limit} EPDs")
                        break

                    # Check if there are more pages
                    if not response.get('next'):
                        logger.info("Reached last page of EPDs")
                        break

                    # Increment offset for next batch
                    offset += batch_size

                    # Small delay to respect rate limits
                    await asyncio.sleep(0.1)

                logger.info(f"Total EPDs fetched: {len(all_epds)}")
                return all_epds

        except Exception as e:
            logger.error(f"Error fetching EPDs: {e}", exc_info=True)
            raise

    async def process_epd_batch(
        self,
        epds: List[Dict[str, Any]],
        session,
        data_source: DataSource
    ) -> None:
        """Process a batch of EPDs: parse, store, chunk, and embed."""
        logger.info(f"Processing batch of {len(epds)} EPDs...")

        for epd_data in epds:
            try:
                await self.process_single_epd(epd_data, session, data_source)
                self.stats['total_processed'] += 1

            except Exception as e:
                self.stats['total_errors'] += 1
                logger.error(f"Error processing EPD {epd_data.get('id', 'unknown')}: {e}", exc_info=True)
                continue

        # Commit batch
        await session.commit()
        logger.info(f"Batch committed. Stats: {self.format_stats()}")

    async def process_single_epd(
        self,
        epd_data: Dict[str, Any],
        session,
        data_source: DataSource
    ) -> None:
        """Process a single EPD: parse, store, chunk, and embed."""
        ec3_id = epd_data.get('id')
        if not ec3_id:
            logger.warning("EPD missing ID, skipping")
            return

        # Check if already exists
        if self.skip_existing:
            result = await session.execute(
                select(CarbonEntity).where(
                    and_(
                        CarbonEntity.source_id == data_source.id,
                        CarbonEntity.raw_data['id'].astext == str(ec3_id)
                    )
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                self.stats['total_skipped'] += 1
                logger.debug(f"Skipping existing EPD {ec3_id}")
                return

        # Parse EPD using EC3EPDParser
        parser = EC3EPDParser(epd_data)
        entity_data = parser.to_carbon_entity()
        verification_data = parser.to_verification_entity()

        # Create or update CarbonEntity
        entity = CarbonEntity(
            source_id=data_source.id,
            entity_type='product',  # EPDs are products
            name=entity_data.get('name'),
            description=entity_data.get('description'),
            category_hierarchy=entity_data.get('category_hierarchy', []),
            geographic_scope=entity_data.get('geographic_scope'),
            temporal_validity=entity_data.get('temporal_validity'),
            quality_score=entity_data.get('quality_score', 0.7),
            confidence_level=entity_data.get('confidence_level', 'medium'),
            validation_status='pending',
            raw_data=epd_data,  # Store full EPD data
            extra_metadata=entity_data.get('extra_metadata', {})
        )

        # Add taxonomy codes if available
        if entity_data.get('unspsc_code'):
            entity.unspsc_code = entity_data['unspsc_code']

        session.add(entity)
        await session.flush()  # Get entity.id

        # Create CarbonEntityVerification if we have verification data
        if verification_data:
            verification = CarbonEntityVerification(
                entity_id=entity.id,
                epd_registration_number=verification_data.get('epd_registration_number'),
                openepd_id=verification_data.get('openepd_id'),
                third_party_verified=verification_data.get('third_party_verified', False),
                verification_status=verification_data.get('verification_status', 'pending'),
                gwp_total=verification_data.get('gwp_total'),
                gwp_co2=verification_data.get('gwp_co2'),
                gwp_ch4=verification_data.get('gwp_ch4'),
                gwp_n2o=verification_data.get('gwp_n2o'),
                gwp_biogenic=verification_data.get('gwp_biogenic'),
                gwp_fossil=verification_data.get('gwp_fossil'),
                lca_stages_included=verification_data.get('lca_stages_included', []),
                lca_stage_emissions=verification_data.get('lca_stage_emissions', {}),
                published_date=verification_data.get('published_date'),
                valid_from_date=verification_data.get('valid_from_date'),
                expiry_date=verification_data.get('expiry_date'),
                environmental_indicators=verification_data.get('environmental_indicators', {}),
                material_composition=verification_data.get('material_composition', {}),
                extra_metadata=verification_data.get('extra_metadata', {})
            )
            session.add(verification)

        # Create EmissionFactor if we have GWP data
        gwp_total = verification_data.get('gwp_total') if verification_data else None
        if gwp_total:
            emission_factor = EmissionFactor(
                entity_id=entity.id,
                value=float(gwp_total),
                unit='kg CO2e',
                scope='3',  # EPDs typically focus on lifecycle (Scope 3)
                lifecycle_stage='cradle_to_grave',
                accounting_standard='ISO_14067',
                geographic_scope=entity_data.get('geographic_scope'),
                quality_score=entity_data.get('quality_score', 0.7)
            )
            session.add(emission_factor)

        await session.flush()
        self.stats['total_inserted'] += 1

        # Generate searchable text for chunking
        # Prepare entity data dict for searchable text generation
        entity_dict = {
            'name': entity.name,
            'description': entity.description,
            'entity_type': entity.entity_type,
            'category_hierarchy': entity.category_hierarchy,
            'geographic_scope': entity.geographic_scope,
            'custom_tags': [],
            'extra_metadata': entity.extra_metadata,
            'raw_data': entity.raw_data
        }
        searchable_text = create_searchable_text_for_chunking(entity_dict)

        # Check if we need to chunk
        if self.text_chunker.should_chunk(searchable_text):
            # Chunk and embed
            await self._chunk_and_embed(entity.id, searchable_text, entity_dict, session)
        else:
            # Just embed the entity directly
            await self.vector_manager.embed_and_store_entity(entity.id, entity_dict)
            self.stats['total_embedded'] += 1

    async def _chunk_and_embed(
        self,
        entity_id,
        text: str,
        entity_dict: Dict[str, Any],
        session
    ) -> None:
        """Chunk text and create embeddings for each chunk."""
        chunks = self.text_chunker.chunk_text(text, entity_id=entity_id)
        logger.debug(f"Created {len(chunks)} chunks for entity {entity_id}")

        for chunk_meta in chunks:
            # Create DocumentChunk
            doc_chunk = DocumentChunk(
                entity_id=entity_id,
                chunk_index=chunk_meta['chunk_index'],
                total_chunks=chunk_meta['total_chunks'],
                chunk_text=chunk_meta['chunk_text'],
                chunk_size=chunk_meta['chunk_size'],
                start_position=chunk_meta['start_position'],
                end_position=chunk_meta['end_position'],
                overlap_before=chunk_meta['overlap_before'],
                overlap_after=chunk_meta['overlap_after']
            )
            session.add(doc_chunk)
            await session.flush()

            # Generate embedding for chunk
            embedding = await self.vector_manager.generate_embedding(chunk_meta['chunk_text'])
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'

            # Store embedding using raw asyncpg
            conn = await session.connection()
            raw_conn = await conn.get_raw_connection()
            sql = """
                UPDATE document_chunks
                SET embedding = $1::vector
                WHERE id = $2
            """
            await raw_conn.driver_connection.execute(sql, embedding_str, doc_chunk.id)

            self.stats['total_chunks'] += 1

        # Also embed the entity itself with a summary
        await self.vector_manager.embed_and_store_entity(entity_id, entity_dict)
        self.stats['total_embedded'] += 1

    def format_stats(self) -> str:
        """Format statistics for logging."""
        elapsed = (datetime.now(UTC) - self.stats['start_time']).total_seconds()
        rate = self.stats['total_processed'] / elapsed if elapsed > 0 else 0

        return (
            f"Fetched: {self.stats['total_fetched']}, "
            f"Processed: {self.stats['total_processed']}, "
            f"Inserted: {self.stats['total_inserted']}, "
            f"Embedded: {self.stats['total_embedded']}, "
            f"Chunks: {self.stats['total_chunks']}, "
            f"Skipped: {self.stats['total_skipped']}, "
            f"Errors: {self.stats['total_errors']}, "
            f"Rate: {rate:.2f}/sec"
        )

    async def run(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Main execution pipeline."""
        logger.info("=" * 80)
        logger.info("EPD VECTOR STORE LOADER")
        logger.info("=" * 80)
        logger.info(f"Configuration:")
        logger.info(f"  Batch size: {self.batch_size}")
        logger.info(f"  Skip existing: {self.skip_existing}")
        logger.info(f"  Limit: {limit or 'None'}")
        logger.info("=" * 80)

        try:
            # Step 1: Fetch all EPDs
            epds = await self.fetch_all_epds(limit=limit)
            if not epds:
                logger.warning("No EPDs fetched. Exiting.")
                return self.stats

            # Step 2: Process in batches
            async with AsyncSessionLocal() as session:
                # Get or create data source
                data_source = await self.get_or_create_data_source(session)

                # Process EPDs in batches
                for i in range(0, len(epds), self.batch_size):
                    batch = epds[i:i + self.batch_size]
                    batch_num = (i // self.batch_size) + 1
                    total_batches = (len(epds) + self.batch_size - 1) // self.batch_size

                    logger.info(f"Processing batch {batch_num}/{total_batches}...")
                    await self.process_epd_batch(batch, session, data_source)

            # Final statistics
            elapsed = (datetime.now(UTC) - self.stats['start_time']).total_seconds()
            logger.info("=" * 80)
            logger.info("COMPLETED!")
            logger.info("=" * 80)
            logger.info(f"Final Statistics:")
            logger.info(f"  Total EPDs fetched: {self.stats['total_fetched']}")
            logger.info(f"  Total processed: {self.stats['total_processed']}")
            logger.info(f"  Total inserted: {self.stats['total_inserted']}")
            logger.info(f"  Total embedded: {self.stats['total_embedded']}")
            logger.info(f"  Total chunks created: {self.stats['total_chunks']}")
            logger.info(f"  Total skipped: {self.stats['total_skipped']}")
            logger.info(f"  Total errors: {self.stats['total_errors']}")
            logger.info(f"  Elapsed time: {elapsed:.2f}s")
            logger.info(f"  Processing rate: {self.stats['total_processed']/elapsed:.2f} EPDs/sec")
            logger.info("=" * 80)

            return self.stats

        except Exception as e:
            logger.error(f"Fatal error in pipeline: {e}", exc_info=True)
            raise


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Load EPDs from EC3 into vector store")
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of EPDs to process (default: all)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Batch size for processing (default: 50)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip EPDs that already exist in database'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )

    args = parser.parse_args()

    # Set log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Initialize components
    ec3_client = EC3Client()
    vector_manager = VectorManager()
    text_chunker = TextChunker(
        chunk_size=1500,
        overlap=200,
        max_seq_length=512
    )

    # Create loader
    loader = EPDVectorLoader(
        ec3_client=ec3_client,
        vector_manager=vector_manager,
        text_chunker=text_chunker,
        batch_size=args.batch_size,
        skip_existing=args.skip_existing
    )

    # Run pipeline
    try:
        stats = await loader.run(limit=args.limit)

        # Exit with appropriate code
        if stats['total_errors'] > 0:
            logger.warning(f"Completed with {stats['total_errors']} errors")
            sys.exit(1)
        else:
            logger.info("Completed successfully!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
