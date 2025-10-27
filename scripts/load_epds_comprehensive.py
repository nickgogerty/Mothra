#!/usr/bin/env python3
"""
Comprehensive EPD Vector Store Loader with Detailed Tracking
=============================================================
Enhanced version of EPD loader with extensive logging, progress tracking,
and detailed confirmation of all operations.

Features:
- Real-time progress tracking with percentage completion
- Detailed logging of each EPD being processed
- Category and geography statistics
- Chunking and embedding confirmation
- Comprehensive final report with breakdowns by type
- Individual EPD details in JSON log file

Usage:
    python scripts/load_epds_comprehensive.py [--limit N] [--batch-size N] [--skip-existing]
"""

import asyncio
import argparse
import sys
import logging
import os
from pathlib import Path
from datetime import datetime, UTC
from typing import List, Dict, Any, Optional
from collections import defaultdict
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

from mothra.agents.discovery.ec3_integration import EC3Client, EC3EPDParser
from mothra.agents.embedding.vector_manager import VectorManager
from mothra.utils.text_chunker import TextChunker, create_searchable_text_for_chunking
from mothra.db.session import AsyncSessionLocal
from mothra.db.models import CarbonEntity, EmissionFactor, DataSource
from mothra.db.models_verification import CarbonEntityVerification
from mothra.db.models_chunks import DocumentChunk
from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert


# Configure logging with both file and console handlers
log_dir = Path(__file__).parent.parent / 'logs'
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
detailed_log_file = log_dir / f'epd_loading_detailed_{timestamp}.log'
summary_log_file = log_dir / f'epd_loading_summary_{timestamp}.log'
epd_details_file = log_dir / f'epd_details_{timestamp}.jsonl'

# Main logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(detailed_log_file)
    ]
)
logger = logging.getLogger(__name__)

# Summary logger (only important milestones)
summary_logger = logging.getLogger('summary')
summary_logger.setLevel(logging.INFO)
summary_handler = logging.FileHandler(summary_log_file)
summary_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
summary_logger.addHandler(summary_handler)


class ComprehensiveEPDVectorLoader:
    """Enhanced EPD loader with comprehensive tracking and reporting."""

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

        # Statistics tracking
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

        # Detailed tracking
        self.epd_details = []
        self.category_counts = defaultdict(int)
        self.geography_counts = defaultdict(int)
        self.verification_counts = defaultdict(int)
        self.chunking_stats = {
            'entities_chunked': 0,
            'entities_not_chunked': 0,
            'total_chunks_created': 0,
            'avg_chunks_per_entity': 0,
            'max_chunks': 0,
            'min_chunks': float('inf')
        }
        self.embedding_stats = {
            'embeddings_generated': 0,
            'embedding_dimensions': 384,
            'avg_embedding_time_ms': 0,
            'total_embedding_time': 0
        }
        self.error_details = []

    def log_progress(self, current: int, total: int, message: str = ""):
        """Log progress with percentage."""
        percentage = (current / total * 100) if total > 0 else 0
        bar_length = 40
        filled = int(bar_length * current // total) if total > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)

        progress_msg = f"Progress: [{bar}] {percentage:.1f}% ({current}/{total}) {message}"
        logger.info(progress_msg)
        summary_logger.info(progress_msg)

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
            logger.info(f"✓ Created data source: {source.name} (ID: {source.id})")
            summary_logger.info(f"Created data source: {source.name}")

        return source

    async def fetch_all_epds(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fetch all EPDs from EC3 API with detailed progress tracking."""
        logger.info("=" * 80)
        logger.info("STARTING EPD EXTRACTION FROM EC3 API")
        logger.info("=" * 80)
        summary_logger.info("Starting EPD extraction from EC3 API")

        try:
            async with self.ec3_client as client:
                # Validate credentials
                validation_result = await client.validate_credentials()
                if not validation_result.get('valid'):
                    error_msg = (
                        f"EC3 API credentials are invalid: {validation_result.get('message')}. "
                        f"Auth method: {validation_result.get('auth_method')}"
                    )
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                auth_method = validation_result.get('auth_method')
                logger.info(f"✓ EC3 credentials validated successfully ({auth_method})")
                summary_logger.info(f"Credentials validated: {auth_method}")

                # Fetch EPDs with pagination
                all_epds = []
                offset = 0
                batch_size = 100

                while True:
                    logger.info(f"\n--- Fetching EPD batch at offset {offset} ---")

                    response = await client.search_epds(
                        limit=batch_size,
                        offset=offset
                    )

                    if not response or 'results' not in response:
                        logger.warning(f"No results in response at offset {offset}")
                        break

                    epds = response['results']
                    if not epds:
                        logger.info("✓ No more EPDs to fetch - reached end")
                        break

                    all_epds.extend(epds)
                    self.stats['total_fetched'] = len(all_epds)

                    # Log details about this batch
                    logger.info(f"✓ Fetched {len(epds)} EPDs in this batch")
                    for i, epd in enumerate(epds[:3]):  # Show first 3 as samples
                        epd_name = epd.get('name', 'Unknown')
                        epd_id = epd.get('id', 'Unknown')
                        logger.info(f"  Sample {i+1}: {epd_name} (ID: {epd_id})")

                    if len(epds) > 3:
                        logger.info(f"  ... and {len(epds) - 3} more in this batch")

                    # Progress update
                    self.log_progress(len(all_epds), limit or 90000, f"- Fetched {len(all_epds)} EPDs")

                    # Check if we've hit the limit
                    if limit and len(all_epds) >= limit:
                        all_epds = all_epds[:limit]
                        logger.info(f"✓ Reached limit of {limit} EPDs")
                        summary_logger.info(f"Reached limit: {limit} EPDs")
                        break

                    # Check if there are more pages
                    if not response.get('next'):
                        logger.info("✓ Reached last page of EPDs")
                        summary_logger.info("Reached last page of EPDs")
                        break

                    offset += batch_size
                    await asyncio.sleep(0.1)  # Rate limiting

                logger.info(f"\n{'=' * 80}")
                logger.info(f"✓ TOTAL EPDs FETCHED: {len(all_epds)}")
                logger.info(f"{'=' * 80}\n")
                summary_logger.info(f"Total EPDs fetched: {len(all_epds)}")

                return all_epds

        except Exception as e:
            logger.error(f"✗ Error fetching EPDs: {e}", exc_info=True)
            summary_logger.error(f"Error fetching EPDs: {e}")
            raise

    async def process_epd_batch(
        self,
        epds: List[Dict[str, Any]],
        session,
        data_source: DataSource,
        batch_num: int,
        total_batches: int
    ) -> None:
        """Process a batch of EPDs with detailed tracking."""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"PROCESSING BATCH {batch_num}/{total_batches} ({len(epds)} EPDs)")
        logger.info(f"{'=' * 80}")
        summary_logger.info(f"Processing batch {batch_num}/{total_batches}")

        for idx, epd_data in enumerate(epds, 1):
            try:
                logger.info(f"\n--- EPD {idx}/{len(epds)} in batch {batch_num} ---")
                await self.process_single_epd(epd_data, session, data_source, batch_num, idx)
                self.stats['total_processed'] += 1

            except Exception as e:
                self.stats['total_errors'] += 1
                epd_id = epd_data.get('id', 'unknown')
                epd_name = epd_data.get('name', 'Unknown')
                error_detail = {
                    'epd_id': epd_id,
                    'epd_name': epd_name,
                    'batch': batch_num,
                    'error': str(e)
                }
                self.error_details.append(error_detail)
                logger.error(f"✗ Error processing EPD {epd_id} ({epd_name}): {e}", exc_info=True)
                continue

        # Commit batch
        await session.commit()
        logger.info(f"\n✓ Batch {batch_num} committed successfully")
        logger.info(f"  Stats: {self.format_stats()}")
        summary_logger.info(f"Batch {batch_num} completed: {self.format_stats()}")

    async def process_single_epd(
        self,
        epd_data: Dict[str, Any],
        session,
        data_source: DataSource,
        batch_num: int,
        epd_idx: int
    ) -> None:
        """Process a single EPD with comprehensive logging."""
        ec3_id = epd_data.get('id')
        epd_name = epd_data.get('name', 'Unknown')

        if not ec3_id:
            logger.warning("✗ EPD missing ID, skipping")
            return

        logger.info(f"Processing: {epd_name}")
        logger.info(f"  EC3 ID: {ec3_id}")

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
                logger.info(f"  ⊘ Skipped (already exists)")
                return

        # Parse EPD
        start_parse = datetime.now()
        parser = EC3EPDParser()
        entity_data, verification_data = parser.parse_epd_to_entity(epd_data, data_source)
        parse_time = (datetime.now() - start_parse).total_seconds()

        logger.info(f"  ✓ Parsed in {parse_time:.3f}s")

        # Extract and log key information
        category = entity_data.get('category_hierarchy', ['Unknown'])[0] if entity_data.get('category_hierarchy') else 'Unknown'
        geography = entity_data.get('geographic_scope', ['Unknown'])[0] if entity_data.get('geographic_scope') else 'Unknown'
        gwp_total = verification_data.get('gwp_total') if verification_data else None

        self.category_counts[category] += 1
        self.geography_counts[geography] += 1

        logger.info(f"  Category: {category}")
        logger.info(f"  Geography: {geography}")
        if gwp_total:
            logger.info(f"  GWP Total: {gwp_total} kg CO2e")

        # Create CarbonEntity
        entity = CarbonEntity(
            source_id=data_source.id,
            entity_type='product',
            name=entity_data.get('name'),
            description=entity_data.get('description'),
            category_hierarchy=entity_data.get('category_hierarchy', []),
            geographic_scope=entity_data.get('geographic_scope'),
            temporal_validity=entity_data.get('temporal_validity'),
            quality_score=entity_data.get('quality_score', 0.7),
            confidence_level=entity_data.get('confidence_level', 'medium'),
            validation_status='pending',
            raw_data=epd_data,
            extra_metadata=entity_data.get('extra_metadata', {})
        )

        if entity_data.get('unspsc_code'):
            entity.unspsc_code = entity_data['unspsc_code']

        session.add(entity)
        await session.flush()

        logger.info(f"  ✓ Entity created (ID: {entity.id})")

        # Create verification record
        if verification_data:
            verification_status = verification_data.get('verification_status', 'pending')
            self.verification_counts[verification_status] += 1

            verification = CarbonEntityVerification(
                entity_id=entity.id,
                epd_registration_number=verification_data.get('epd_registration_number'),
                openepd_id=verification_data.get('openepd_id'),
                third_party_verified=verification_data.get('third_party_verified', False),
                verification_status=verification_status,
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
            logger.info(f"  ✓ Verification record created (status: {verification_status})")

        # Create emission factor
        if gwp_total:
            emission_factor = EmissionFactor(
                entity_id=entity.id,
                value=float(gwp_total),
                unit='kg CO2e',
                scope='3',
                lifecycle_stage='cradle_to_grave',
                accounting_standard='ISO_14067',
                geographic_scope=entity_data.get('geographic_scope'),
                quality_score=entity_data.get('quality_score', 0.7)
            )
            session.add(emission_factor)
            logger.info(f"  ✓ Emission factor created")

        await session.flush()
        self.stats['total_inserted'] += 1

        # Chunking and embedding
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
        text_length = len(searchable_text)

        logger.info(f"  Text length: {text_length} characters")

        # Check if chunking is needed
        start_embed = datetime.now()
        if self.text_chunker.should_chunk(searchable_text):
            num_chunks = await self._chunk_and_embed(entity.id, searchable_text, entity_dict, session)
            self.chunking_stats['entities_chunked'] += 1
            self.chunking_stats['total_chunks_created'] += num_chunks
            self.chunking_stats['max_chunks'] = max(self.chunking_stats['max_chunks'], num_chunks)
            self.chunking_stats['min_chunks'] = min(self.chunking_stats['min_chunks'], num_chunks)
            logger.info(f"  ✓ Chunked into {num_chunks} pieces")
        else:
            await self.vector_manager.embed_and_store_entity(entity.id, entity_dict)
            self.stats['total_embedded'] += 1
            self.chunking_stats['entities_not_chunked'] += 1
            logger.info(f"  ✓ Embedded without chunking")

        embed_time = (datetime.now() - start_embed).total_seconds()
        self.embedding_stats['total_embedding_time'] += embed_time
        self.embedding_stats['embeddings_generated'] += 1
        logger.info(f"  ✓ Embedding completed in {embed_time:.3f}s")

        # Store detailed EPD info
        epd_detail = {
            'ec3_id': ec3_id,
            'entity_id': str(entity.id),
            'name': epd_name,
            'category': category,
            'geography': geography,
            'gwp_total': gwp_total,
            'text_length': text_length,
            'chunked': self.text_chunker.should_chunk(searchable_text),
            'num_chunks': num_chunks if self.text_chunker.should_chunk(searchable_text) else 0,
            'batch': batch_num,
            'processing_time_ms': (parse_time + embed_time) * 1000
        }
        self.epd_details.append(epd_detail)

        # Write to JSONL file
        with open(epd_details_file, 'a') as f:
            f.write(json.dumps(epd_detail) + '\n')

    async def _chunk_and_embed(
        self,
        entity_id,
        text: str,
        entity_dict: Dict[str, Any],
        session
    ) -> int:
        """Chunk text and create embeddings for each chunk."""
        chunks = self.text_chunker.chunk_text(text, entity_id=entity_id)

        for chunk_meta in chunks:
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

            # Generate embedding
            embedding = await self.vector_manager.generate_embedding(chunk_meta['chunk_text'])
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'

            # Store embedding
            conn = await session.connection()
            raw_conn = await conn.get_raw_connection()
            sql = """
                UPDATE document_chunks
                SET embedding = $1::vector
                WHERE id = $2
            """
            await raw_conn.driver_connection.execute(sql, embedding_str, doc_chunk.id)

            self.stats['total_chunks'] += 1

        # Embed entity itself
        await self.vector_manager.embed_and_store_entity(entity_id, entity_dict)
        self.stats['total_embedded'] += 1

        return len(chunks)

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

    def generate_final_report(self) -> str:
        """Generate comprehensive final report."""
        elapsed = (datetime.now(UTC) - self.stats['start_time']).total_seconds()
        avg_rate = self.stats['total_processed'] / elapsed if elapsed > 0 else 0

        # Calculate chunking averages
        if self.chunking_stats['entities_chunked'] > 0:
            self.chunking_stats['avg_chunks_per_entity'] = (
                self.chunking_stats['total_chunks_created'] /
                self.chunking_stats['entities_chunked']
            )

        # Calculate embedding averages
        if self.embedding_stats['embeddings_generated'] > 0:
            self.embedding_stats['avg_embedding_time_ms'] = (
                self.embedding_stats['total_embedding_time'] * 1000 /
                self.embedding_stats['embeddings_generated']
            )

        report = f"""
{'=' * 80}
COMPREHENSIVE EPD LOADING REPORT
{'=' * 80}

OVERALL STATISTICS
------------------
Total EPDs Fetched:          {self.stats['total_fetched']:,}
Total Processed:             {self.stats['total_processed']:,}
Total Inserted:              {self.stats['total_inserted']:,}
Total Embedded:              {self.stats['total_embedded']:,}
Total Chunks Created:        {self.stats['total_chunks']:,}
Total Skipped:               {self.stats['total_skipped']:,}
Total Errors:                {self.stats['total_errors']:,}

PERFORMANCE METRICS
-------------------
Total Time:                  {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)
Average Rate:                {avg_rate:.2f} EPDs/second
Time per EPD:                {elapsed/self.stats['total_processed']:.3f} seconds

CHUNKING STATISTICS
-------------------
Entities Chunked:            {self.chunking_stats['entities_chunked']:,}
Entities Not Chunked:        {self.chunking_stats['entities_not_chunked']:,}
Total Chunks Created:        {self.chunking_stats['total_chunks_created']:,}
Avg Chunks per Entity:       {self.chunking_stats['avg_chunks_per_entity']:.2f}
Max Chunks (single EPD):     {self.chunking_stats['max_chunks']}
Min Chunks (single EPD):     {self.chunking_stats['min_chunks'] if self.chunking_stats['min_chunks'] != float('inf') else 0}

EMBEDDING STATISTICS
--------------------
Embeddings Generated:        {self.embedding_stats['embeddings_generated']:,}
Embedding Dimensions:        {self.embedding_stats['embedding_dimensions']}
Avg Embedding Time:          {self.embedding_stats['avg_embedding_time_ms']:.2f} ms
Total Embedding Time:        {self.embedding_stats['total_embedding_time']:.2f} seconds

CATEGORY BREAKDOWN
------------------
"""
        # Top 10 categories
        top_categories = sorted(self.category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for category, count in top_categories:
            report += f"  {category:30s}: {count:5d} ({count/self.stats['total_processed']*100:.1f}%)\n"

        report += f"""
GEOGRAPHY BREAKDOWN
-------------------
"""
        # Top 10 geographies
        top_geographies = sorted(self.geography_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        for geography, count in top_geographies:
            report += f"  {geography:30s}: {count:5d} ({count/self.stats['total_processed']*100:.1f}%)\n"

        report += f"""
VERIFICATION STATUS
-------------------
"""
        for status, count in sorted(self.verification_counts.items(), key=lambda x: x[1], reverse=True):
            report += f"  {status:30s}: {count:5d} ({count/self.stats['total_processed']*100:.1f}%)\n"

        if self.error_details:
            report += f"""
ERRORS ENCOUNTERED
------------------
Total Errors: {len(self.error_details)}

"""
            for i, error in enumerate(self.error_details[:10], 1):  # Show first 10
                report += f"{i}. EPD: {error['epd_name']} (ID: {error['epd_id']})\n"
                report += f"   Batch: {error['batch']}\n"
                report += f"   Error: {error['error']}\n\n"

            if len(self.error_details) > 10:
                report += f"... and {len(self.error_details) - 10} more errors\n\n"

        report += f"""
OUTPUT FILES
------------
Detailed Log:     {detailed_log_file}
Summary Log:      {summary_log_file}
EPD Details:      {epd_details_file}

{'=' * 80}
"""
        return report

    async def run(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Main execution pipeline."""
        logger.info("\n" + "=" * 80)
        logger.info("COMPREHENSIVE EPD VECTOR STORE LOADER")
        logger.info("=" * 80)
        logger.info(f"Configuration:")
        logger.info(f"  Batch size:      {self.batch_size}")
        logger.info(f"  Skip existing:   {self.skip_existing}")
        logger.info(f"  Limit:           {limit or 'All EPDs'}")
        logger.info(f"  Embedding model: sentence-transformers/all-MiniLM-L6-v2")
        logger.info(f"  Embedding dims:  384")
        logger.info(f"  Chunk size:      1500 chars")
        logger.info(f"  Chunk overlap:   200 chars")
        logger.info("=" * 80 + "\n")
        summary_logger.info("EPD Vector Store Loader Started")

        try:
            # Step 1: Fetch all EPDs
            epds = await self.fetch_all_epds(limit=limit)
            if not epds:
                logger.warning("No EPDs fetched. Exiting.")
                summary_logger.warning("No EPDs fetched")
                return self.stats

            # Step 2: Process in batches
            async with AsyncSessionLocal() as session:
                data_source = await self.get_or_create_data_source(session)

                total_batches = (len(epds) + self.batch_size - 1) // self.batch_size

                for i in range(0, len(epds), self.batch_size):
                    batch = epds[i:i + self.batch_size]
                    batch_num = (i // self.batch_size) + 1

                    await self.process_epd_batch(batch, session, data_source, batch_num, total_batches)

                    # Progress update
                    self.log_progress(
                        self.stats['total_processed'],
                        len(epds),
                        f"- Batch {batch_num}/{total_batches} complete"
                    )

            # Generate and display final report
            report = self.generate_final_report()
            logger.info(report)
            summary_logger.info("EPD loading completed successfully")

            # Write report to file
            report_file = log_dir / f'epd_loading_report_{timestamp}.txt'
            with open(report_file, 'w') as f:
                f.write(report)

            logger.info(f"\n✓ Full report saved to: {report_file}\n")

            return self.stats

        except Exception as e:
            logger.error(f"✗ Fatal error in pipeline: {e}", exc_info=True)
            summary_logger.error(f"Pipeline failed: {e}")
            raise


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive EPD loader with detailed tracking",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
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
    loader = ComprehensiveEPDVectorLoader(
        ec3_client=ec3_client,
        vector_manager=vector_manager,
        text_chunker=text_chunker,
        batch_size=args.batch_size,
        skip_existing=args.skip_existing
    )

    # Run pipeline
    try:
        stats = await loader.run(limit=args.limit)

        if stats['total_errors'] > 0:
            logger.warning(f"Completed with {stats['total_errors']} errors")
            sys.exit(1)
        else:
            logger.info("✓ Completed successfully!")
            sys.exit(0)

    except Exception as e:
        logger.error(f"✗ Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
