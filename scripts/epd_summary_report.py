#!/usr/bin/env python3
"""
EPD Vector Store Summary Report
================================
Generates a comprehensive summary of EPDs currently loaded in the vector store.

This script queries the database and provides:
- Total counts of EPDs, chunks, and embeddings
- Breakdown by category, geography, and verification status
- Quality metrics and statistics
- Sample EPDs from each category
- Vector store health metrics

Usage:
    python scripts/epd_summary_report.py [--output-file report.txt] [--format text|json]
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

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

from mothra.db.session import AsyncSessionLocal
from mothra.db.models import CarbonEntity, EmissionFactor, DataSource
from mothra.db.models_verification import CarbonEntityVerification
from mothra.db.models_chunks import DocumentChunk
from sqlalchemy import select, func, and_, text
from sqlalchemy.orm import selectinload


class EPDSummaryReporter:
    """Generates comprehensive summary reports of EPD data in vector store."""

    def __init__(self):
        self.report_data = {}

    async def gather_statistics(self) -> Dict[str, Any]:
        """Gather all statistics from the database."""
        async with AsyncSessionLocal() as session:
            print("Gathering EPD statistics from database...")

            # Overall counts
            print("  - Counting EPDs...")
            total_epds = await session.scalar(
                select(func.count()).select_from(CarbonEntity)
            )

            total_verified = await session.scalar(
                select(func.count()).select_from(CarbonEntityVerification)
            )

            total_chunks = await session.scalar(
                select(func.count()).select_from(DocumentChunk)
            )

            total_emission_factors = await session.scalar(
                select(func.count()).select_from(EmissionFactor)
            )

            # Count embeddings (entities with non-null embeddings)
            print("  - Counting embeddings...")
            entities_with_embeddings = await session.scalar(
                select(func.count()).select_from(CarbonEntity).where(
                    CarbonEntity.embedding.isnot(None)
                )
            )

            chunks_with_embeddings = await session.scalar(
                select(func.count()).select_from(DocumentChunk).where(
                    DocumentChunk.embedding.isnot(None)
                )
            )

            # Category breakdown
            print("  - Analyzing categories...")
            category_query = select(
                func.unnest(CarbonEntity.category_hierarchy).label('category'),
                func.count().label('count')
            ).group_by('category').order_by(func.count().desc())

            category_result = await session.execute(category_query)
            categories = {row.category: row.count for row in category_result}

            # Geography breakdown
            print("  - Analyzing geographies...")
            geography_query = select(
                func.unnest(CarbonEntity.geographic_scope).label('geography'),
                func.count().label('count')
            ).group_by('geography').order_by(func.count().desc())

            geography_result = await session.execute(geography_query)
            geographies = {row.geography: row.count for row in geography_result}

            # Verification status breakdown
            print("  - Analyzing verification status...")
            verification_query = select(
                CarbonEntityVerification.verification_status,
                func.count().label('count')
            ).group_by(CarbonEntityVerification.verification_status)

            verification_result = await session.execute(verification_query)
            verification_statuses = {row.verification_status: row.count for row in verification_result}

            # Quality metrics
            print("  - Calculating quality metrics...")
            quality_query = select(
                func.avg(CarbonEntity.quality_score).label('avg_quality'),
                func.min(CarbonEntity.quality_score).label('min_quality'),
                func.max(CarbonEntity.quality_score).label('max_quality')
            )
            quality_result = await session.execute(quality_query)
            quality_row = quality_result.first()

            # GWP statistics
            print("  - Analyzing GWP values...")
            gwp_query = select(
                func.avg(CarbonEntityVerification.gwp_total).label('avg_gwp'),
                func.min(CarbonEntityVerification.gwp_total).label('min_gwp'),
                func.max(CarbonEntityVerification.gwp_total).label('max_gwp'),
                func.count(CarbonEntityVerification.gwp_total).label('count_gwp')
            ).where(CarbonEntityVerification.gwp_total.isnot(None))

            gwp_result = await session.execute(gwp_query)
            gwp_row = gwp_result.first()

            # Chunking statistics
            print("  - Analyzing chunking patterns...")
            chunking_query = select(
                func.count(func.distinct(DocumentChunk.entity_id)).label('entities_with_chunks'),
                func.avg(DocumentChunk.total_chunks).label('avg_chunks'),
                func.max(DocumentChunk.total_chunks).label('max_chunks'),
                func.avg(DocumentChunk.chunk_size).label('avg_chunk_size')
            )
            chunking_result = await session.execute(chunking_query)
            chunking_row = chunking_result.first()

            # Get sample EPDs from each major category
            print("  - Fetching sample EPDs...")
            samples = {}
            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]

            for category, _ in top_categories:
                sample_query = select(CarbonEntity).where(
                    CarbonEntity.category_hierarchy.contains([category])
                ).limit(3)

                sample_result = await session.execute(sample_query)
                sample_epds = sample_result.scalars().all()

                samples[category] = [
                    {
                        'id': str(epd.id),
                        'name': epd.name,
                        'description': epd.description[:200] if epd.description else None
                    }
                    for epd in sample_epds
                ]

            # Data source info
            print("  - Gathering data source information...")
            sources_query = select(DataSource)
            sources_result = await session.execute(sources_query)
            sources = sources_result.scalars().all()

            data_sources = [
                {
                    'name': source.name,
                    'url': source.url,
                    'type': source.source_type,
                    'status': source.status
                }
                for source in sources
            ]

            self.report_data = {
                'generated_at': datetime.now().isoformat(),
                'overall_counts': {
                    'total_epds': total_epds,
                    'total_verified_records': total_verified,
                    'total_chunks': total_chunks,
                    'total_emission_factors': total_emission_factors,
                    'entities_with_embeddings': entities_with_embeddings,
                    'chunks_with_embeddings': chunks_with_embeddings,
                    'embedding_coverage': f"{entities_with_embeddings/total_epds*100:.1f}%" if total_epds > 0 else "0%"
                },
                'categories': categories,
                'geographies': geographies,
                'verification_statuses': verification_statuses,
                'quality_metrics': {
                    'average_quality_score': float(quality_row.avg_quality) if quality_row.avg_quality else 0,
                    'min_quality_score': float(quality_row.min_quality) if quality_row.min_quality else 0,
                    'max_quality_score': float(quality_row.max_quality) if quality_row.max_quality else 0
                },
                'gwp_statistics': {
                    'average_gwp': float(gwp_row.avg_gwp) if gwp_row.avg_gwp else 0,
                    'min_gwp': float(gwp_row.min_gwp) if gwp_row.min_gwp else 0,
                    'max_gwp': float(gwp_row.max_gwp) if gwp_row.max_gwp else 0,
                    'count_with_gwp': int(gwp_row.count_gwp) if gwp_row.count_gwp else 0
                },
                'chunking_statistics': {
                    'entities_with_chunks': int(chunking_row.entities_with_chunks) if chunking_row.entities_with_chunks else 0,
                    'entities_without_chunks': total_epds - (int(chunking_row.entities_with_chunks) if chunking_row.entities_with_chunks else 0),
                    'avg_chunks_per_entity': float(chunking_row.avg_chunks) if chunking_row.avg_chunks else 0,
                    'max_chunks': int(chunking_row.max_chunks) if chunking_row.max_chunks else 0,
                    'avg_chunk_size': float(chunking_row.avg_chunk_size) if chunking_row.avg_chunk_size else 0,
                    'total_chunks': total_chunks
                },
                'sample_epds': samples,
                'data_sources': data_sources
            }

            print("✓ Statistics gathered successfully\n")
            return self.report_data

    def generate_text_report(self) -> str:
        """Generate a human-readable text report."""
        data = self.report_data
        overall = data['overall_counts']
        quality = data['quality_metrics']
        gwp = data['gwp_statistics']
        chunking = data['chunking_statistics']

        report = f"""
{'=' * 80}
EPD VECTOR STORE SUMMARY REPORT
{'=' * 80}
Generated: {data['generated_at']}

OVERALL STATISTICS
------------------
Total EPDs in Database:          {overall['total_epds']:,}
Verified Records:                {overall['total_verified_records']:,}
Emission Factors:                {overall['total_emission_factors']:,}
Total Document Chunks:           {overall['total_chunks']:,}

EMBEDDING COVERAGE
------------------
Entities with Embeddings:        {overall['entities_with_embeddings']:,} ({overall['embedding_coverage']})
Chunks with Embeddings:          {overall['chunks_with_embeddings']:,}
Total Embeddings:                {overall['entities_with_embeddings'] + overall['chunks_with_embeddings']:,}

QUALITY METRICS
---------------
Average Quality Score:           {quality['average_quality_score']:.3f}
Min Quality Score:               {quality['min_quality_score']:.3f}
Max Quality Score:               {quality['max_quality_score']:.3f}

GWP (GLOBAL WARMING POTENTIAL) STATISTICS
------------------------------------------
EPDs with GWP Data:              {gwp['count_with_gwp']:,}
Average GWP:                     {gwp['average_gwp']:.2f} kg CO2e
Min GWP:                         {gwp['min_gwp']:.2f} kg CO2e
Max GWP:                         {gwp['max_gwp']:.2f} kg CO2e

CHUNKING STATISTICS
-------------------
Entities with Chunks:            {chunking['entities_with_chunks']:,}
Entities without Chunks:         {chunking['entities_without_chunks']:,}
Average Chunks per Entity:       {chunking['avg_chunks_per_entity']:.2f}
Max Chunks (single EPD):         {chunking['max_chunks']}
Average Chunk Size:              {chunking['avg_chunk_size']:.0f} characters
Total Chunks Created:            {chunking['total_chunks']:,}

CATEGORY BREAKDOWN (Top 15)
----------------------------
"""
        # Top 15 categories
        top_categories = sorted(data['categories'].items(), key=lambda x: x[1], reverse=True)[:15]
        for i, (category, count) in enumerate(top_categories, 1):
            percentage = count / overall['total_epds'] * 100 if overall['total_epds'] > 0 else 0
            report += f"{i:2d}. {category:35s}: {count:6,} ({percentage:5.1f}%)\n"

        report += f"""
GEOGRAPHY BREAKDOWN (Top 15)
-----------------------------
"""
        # Top 15 geographies
        top_geographies = sorted(data['geographies'].items(), key=lambda x: x[1], reverse=True)[:15]
        for i, (geography, count) in enumerate(top_geographies, 1):
            percentage = count / overall['total_epds'] * 100 if overall['total_epds'] > 0 else 0
            report += f"{i:2d}. {geography:35s}: {count:6,} ({percentage:5.1f}%)\n"

        report += f"""
VERIFICATION STATUS
-------------------
"""
        for status, count in sorted(data['verification_statuses'].items(), key=lambda x: x[1], reverse=True):
            percentage = count / overall['total_verified_records'] * 100 if overall['total_verified_records'] > 0 else 0
            report += f"  {status:30s}: {count:6,} ({percentage:5.1f}%)\n"

        report += f"""
DATA SOURCES
------------
"""
        for source in data['data_sources']:
            report += f"  Name:   {source['name']}\n"
            report += f"  URL:    {source['url']}\n"
            report += f"  Type:   {source['type']}\n"
            report += f"  Status: {source['status']}\n\n"

        report += f"""
SAMPLE EPDs BY CATEGORY
-----------------------
"""
        for category, samples in list(data['sample_epds'].items())[:5]:
            report += f"\n{category}:\n"
            for i, sample in enumerate(samples, 1):
                report += f"  {i}. {sample['name']} (ID: {sample['id']})\n"
                if sample['description']:
                    desc = sample['description'][:150] + '...' if len(sample['description']) > 150 else sample['description']
                    report += f"     {desc}\n"

        report += f"""
{'=' * 80}
VECTOR STORE HEALTH
{'=' * 80}
Embedding Coverage:              {overall['embedding_coverage']}
Chunking Rate:                   {chunking['entities_with_chunks']/overall['total_epds']*100:.1f}%
Average Quality:                 {quality['average_quality_score']:.3f}/1.0

RECOMMENDATIONS:
"""
        # Add recommendations based on the data
        if float(overall['embedding_coverage'].rstrip('%')) < 95:
            report += "  ⚠ Embedding coverage is below 95%. Consider re-running embedding generation.\n"
        else:
            report += "  ✓ Excellent embedding coverage.\n"

        if quality['average_quality_score'] < 0.7:
            report += "  ⚠ Average quality score is below 0.7. Review data quality.\n"
        else:
            report += "  ✓ Good average quality score.\n"

        if gwp['count_with_gwp'] / overall['total_epds'] < 0.5 if overall['total_epds'] > 0 else False:
            report += "  ⚠ Less than 50% of EPDs have GWP data. Consider enriching data.\n"
        else:
            report += "  ✓ Good GWP data coverage.\n"

        report += f"""
{'=' * 80}
END OF REPORT
{'=' * 80}
"""
        return report

    def generate_json_report(self) -> str:
        """Generate a JSON report."""
        return json.dumps(self.report_data, indent=2)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive summary report of EPD vector store"
    )
    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='Output file path (default: print to console)'
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )

    args = parser.parse_args()

    try:
        # Create reporter and gather statistics
        reporter = EPDSummaryReporter()
        await reporter.gather_statistics()

        # Generate report
        if args.format == 'json':
            report = reporter.generate_json_report()
        else:
            report = reporter.generate_text_report()

        # Output report
        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
            print(f"✓ Report saved to: {output_path}")
        else:
            print(report)

        sys.exit(0)

    except Exception as e:
        print(f"✗ Error generating report: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
