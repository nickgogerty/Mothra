#!/usr/bin/env python3
"""
Database Summary Report

Shows current MOTHRA database composition:
- Total entities
- Verified EPDs
- Breakdown by source
- Breakdown by category
- Geographic distribution
- Quality metrics
"""

import asyncio
from datetime import datetime

from sqlalchemy import func, select

from mothra.db.models import CarbonEntity, DataSource
from mothra.db.models_verification import CarbonEntityVerification
from mothra.db.session import get_db_context


async def get_database_summary():
    """Generate comprehensive database summary."""
    print("=" * 80)
    print("MOTHRA DATABASE SUMMARY")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    async with get_db_context() as db:
        # ========================================
        # 1. TOTAL COUNTS
        # ========================================
        print("📊 OVERVIEW")
        print("=" * 80)

        # Total entities
        result = await db.execute(select(func.count(CarbonEntity.id)))
        total_entities = result.scalar()
        print(f"Total Entities:        {total_entities:,}")

        # Verified entities
        result = await db.execute(select(func.count(CarbonEntityVerification.id)))
        total_verified = result.scalar()
        print(f"Verified EPDs:         {total_verified:,}")

        # Verification rate
        if total_entities > 0:
            verification_rate = (total_verified / total_entities) * 100
            print(f"Verification Rate:     {verification_rate:.1f}%")
        else:
            print(f"Verification Rate:     0.0%")

        # Data sources count
        result = await db.execute(select(func.count(DataSource.id)))
        total_sources = result.scalar()
        print(f"Data Sources:          {total_sources:,}")
        print()

        # ========================================
        # 2. BREAKDOWN BY SOURCE
        # ========================================
        print("📦 BY DATA SOURCE")
        print("=" * 80)

        stmt = (
            select(
                DataSource.name,
                DataSource.source_type,
                DataSource.category,
                func.count(CarbonEntity.id).label("count"),
            )
            .join(CarbonEntity, CarbonEntity.source_uuid == DataSource.id)
            .group_by(DataSource.name, DataSource.source_type, DataSource.category)
            .order_by(func.count(CarbonEntity.id).desc())
        )

        result = await db.execute(stmt)
        sources = result.all()

        if sources:
            print(f"{'Source Name':<50} {'Type':<20} {'Category':<15} {'Count':>10}")
            print("-" * 95)
            for source in sources:
                name = source.name[:47] + "..." if len(source.name) > 50 else source.name
                print(
                    f"{name:<50} {source.source_type:<20} {source.category:<15} {source.count:>10,}"
                )
        else:
            print("No sources found.")
        print()

        # ========================================
        # 3. BREAKDOWN BY ENTITY TYPE
        # ========================================
        print("🏷️  BY ENTITY TYPE")
        print("=" * 80)

        stmt = (
            select(
                CarbonEntity.entity_type,
                func.count(CarbonEntity.id).label("count"),
            )
            .group_by(CarbonEntity.entity_type)
            .order_by(func.count(CarbonEntity.id).desc())
        )

        result = await db.execute(stmt)
        entity_types = result.all()

        if entity_types:
            for entity_type in entity_types:
                type_name = entity_type.entity_type or "Unknown"
                percentage = (entity_type.count / total_entities) * 100
                print(f"{type_name:<30} {entity_type.count:>10,}  ({percentage:>5.1f}%)")
        else:
            print("No entity types found.")
        print()

        # ========================================
        # 4. BREAKDOWN BY CATEGORY (Top 20)
        # ========================================
        print("📁 BY CATEGORY (Top 20)")
        print("=" * 80)

        stmt = (
            select(
                func.unnest(CarbonEntity.category_hierarchy).label("category"),
                func.count(CarbonEntity.id).label("count"),
            )
            .group_by("category")
            .order_by(func.count(CarbonEntity.id).desc())
            .limit(20)
        )

        result = await db.execute(stmt)
        categories = result.all()

        if categories:
            for category in categories:
                cat_name = category.category or "Unknown"
                percentage = (category.count / total_entities) * 100
                print(f"{cat_name:<30} {category.count:>10,}  ({percentage:>5.1f}%)")
        else:
            print("No categories found.")
        print()

        # ========================================
        # 5. GEOGRAPHIC DISTRIBUTION (Top 15)
        # ========================================
        print("🌍 BY GEOGRAPHY (Top 15)")
        print("=" * 80)

        stmt = (
            select(
                func.unnest(CarbonEntity.geographic_scope).label("geography"),
                func.count(CarbonEntity.id).label("count"),
            )
            .group_by("geography")
            .order_by(func.count(CarbonEntity.id).desc())
            .limit(15)
        )

        result = await db.execute(stmt)
        geographies = result.all()

        if geographies:
            for geo in geographies:
                geo_name = geo.geography or "Unknown"
                percentage = (geo.count / total_entities) * 100
                print(f"{geo_name:<30} {geo.count:>10,}  ({percentage:>5.1f}%)")
        else:
            print("No geographic data found.")
        print()

        # ========================================
        # 6. QUALITY METRICS
        # ========================================
        print("⭐ QUALITY METRICS")
        print("=" * 80)

        # Average quality score
        stmt = select(func.avg(CarbonEntity.quality_score))
        result = await db.execute(stmt)
        avg_quality = result.scalar() or 0.0
        print(f"Average Quality Score: {avg_quality:.2f}")

        # Entities with embeddings
        stmt = select(func.count(CarbonEntity.id)).where(
            CarbonEntity.embedding_384.isnot(None)
        )
        result = await db.execute(stmt)
        entities_with_embeddings = result.scalar()
        embedding_rate = (
            (entities_with_embeddings / total_entities) * 100 if total_entities > 0 else 0
        )
        print(f"Entities with Embeddings: {entities_with_embeddings:,} ({embedding_rate:.1f}%)")
        print()

        # ========================================
        # 7. VERIFICATION DETAILS
        # ========================================
        if total_verified > 0:
            print("✅ VERIFICATION DETAILS")
            print("=" * 80)

            # By verification status
            stmt = (
                select(
                    CarbonEntityVerification.verification_status,
                    func.count(CarbonEntityVerification.id).label("count"),
                )
                .group_by(CarbonEntityVerification.verification_status)
                .order_by(func.count(CarbonEntityVerification.id).desc())
            )

            result = await db.execute(stmt)
            statuses = result.all()

            print("By Verification Status:")
            for status in statuses:
                status_name = status.verification_status or "Unknown"
                percentage = (status.count / total_verified) * 100
                print(f"  {status_name:<25} {status.count:>8,}  ({percentage:>5.1f}%)")
            print()

            # By verification body (Top 10)
            stmt = (
                select(
                    CarbonEntityVerification.verification_body,
                    func.count(CarbonEntityVerification.id).label("count"),
                )
                .where(CarbonEntityVerification.verification_body.isnot(None))
                .group_by(CarbonEntityVerification.verification_body)
                .order_by(func.count(CarbonEntityVerification.id).desc())
                .limit(10)
            )

            result = await db.execute(stmt)
            verifiers = result.all()

            if verifiers:
                print("By Verification Body (Top 10):")
                for verifier in verifiers:
                    v_name = verifier.verification_body[:35]
                    percentage = (verifier.count / total_verified) * 100
                    print(f"  {v_name:<35} {verifier.count:>6,}  ({percentage:>5.1f}%)")
                print()

            # Compliance stats
            stmt = select(
                func.count(CarbonEntityVerification.id)
                .filter(CarbonEntityVerification.iso_14067_compliant == True)
                .label("iso_14067"),
                func.count(CarbonEntityVerification.id)
                .filter(CarbonEntityVerification.en_15804_compliant == True)
                .label("en_15804"),
                func.count(CarbonEntityVerification.id)
                .filter(CarbonEntityVerification.third_party_verified == True)
                .label("third_party"),
            )

            result = await db.execute(stmt)
            compliance = result.one()

            print("Compliance:")
            print(
                f"  ISO 14067 Compliant:     {compliance.iso_14067:>8,}  ({(compliance.iso_14067/total_verified)*100:>5.1f}%)"
            )
            print(
                f"  EN 15804 Compliant:      {compliance.en_15804:>8,}  ({(compliance.en_15804/total_verified)*100:>5.1f}%)"
            )
            print(
                f"  Third-Party Verified:    {compliance.third_party:>8,}  ({(compliance.third_party/total_verified)*100:>5.1f}%)"
            )
            print()

            # GWP statistics
            stmt = select(
                func.avg(CarbonEntityVerification.gwp_total).label("avg_gwp"),
                func.min(CarbonEntityVerification.gwp_total).label("min_gwp"),
                func.max(CarbonEntityVerification.gwp_total).label("max_gwp"),
            ).where(CarbonEntityVerification.gwp_total.isnot(None))

            result = await db.execute(stmt)
            gwp_stats = result.one()

            if gwp_stats.avg_gwp:
                print("GWP (Global Warming Potential) Statistics:")
                print(f"  Average GWP:             {gwp_stats.avg_gwp:>12,.2f} kg CO2e")
                print(f"  Minimum GWP:             {gwp_stats.min_gwp:>12,.2f} kg CO2e")
                print(f"  Maximum GWP:             {gwp_stats.max_gwp:>12,.2f} kg CO2e")
                print()

        # ========================================
        # 8. STORAGE METRICS
        # ========================================
        print("💾 STORAGE METRICS")
        print("=" * 80)

        # Database size (approximate based on table sizes)
        stmt = select(func.count(CarbonEntity.id))
        result = await db.execute(stmt)
        entity_count = result.scalar()

        # Rough estimates (average sizes)
        entity_size = entity_count * 2  # ~2 KB per entity
        verification_size = total_verified * 8  # ~8 KB per verification (with metadata)
        total_size_kb = entity_size + verification_size

        print(f"Approximate Database Size: {total_size_kb:,} KB ({total_size_kb/1024:,.1f} MB)")
        print()

        # ========================================
        # 9. PROGRESS TO GOALS
        # ========================================
        print("🎯 PROGRESS TO GOALS")
        print("=" * 80)

        goal = 100_000
        progress = (total_entities / goal) * 100
        remaining = goal - total_entities

        print(f"Goal:                  {goal:,} entities")
        print(f"Current:               {total_entities:,} entities")
        print(f"Progress:              {progress:.1f}%")
        print(f"Remaining:             {remaining:,} entities")

        # Progress bar
        bar_length = 50
        filled = int((progress / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"[{bar}] {progress:.1f}%")
        print()

        # ========================================
        # 10. RECOMMENDATIONS
        # ========================================
        print("💡 RECOMMENDATIONS")
        print("=" * 80)

        if total_entities < goal:
            needed = goal - total_entities
            print(f"• Run bulk import to add {needed:,} more entities")
            print(f"  Command: python scripts/bulk_import_epds.py")
            print()

        if embedding_rate < 50:
            print(
                f"• Generate embeddings for semantic search ({100-embedding_rate:.0f}% remaining)"
            )
            print(f"  Command: python scripts/chunk_and_embed_all.py")
            print()

        if total_verified == 0:
            print("• Import verified EPDs from EC3 for carbon verification workflows")
            print("  Command: python scripts/bulk_import_epds.py")
            print()

        if total_verified > 0 and embedding_rate >= 90:
            print("✅ Database is well-populated and ready for production!")
            print("  • Test semantic search: python scripts/test_search.py")
            print("  • Query verified EPDs: python scripts/query_epds.py")
            print()

        print("=" * 80)


async def main():
    """Run database summary report."""
    try:
        await get_database_summary()
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
