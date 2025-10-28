#!/usr/bin/env python3
"""
Search for emissions factors and return them in standardized CO2e per unit format.

This script performs semantic search and extracts emission factors from entity metadata.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text

from mothra.db.models import CarbonEntity
from mothra.db.session import get_db_context
from mothra.utils.embeddings import generate_embedding
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


def extract_emission_factor(entity: CarbonEntity) -> dict | None:
    """
    Extract emission factor from entity metadata.

    Args:
        entity: CarbonEntity with potential emission data

    Returns:
        Dict with emission factor info or None
    """
    metadata = entity.extra_metadata

    # Check for emissions_value (from EIA SEDS data)
    if "emissions_value" in metadata:
        return {
            "value": metadata.get("emissions_value"),
            "unit": metadata.get("unit", ""),
            "period": metadata.get("period", ""),
            "fuel_type": metadata.get("fuel_name", ""),
            "sector": metadata.get("sector_name", ""),
            "location": metadata.get("state_name", ""),
        }

    # Check for consumption and generation (from facility data)
    if "consumption" in metadata and "generation" in metadata:
        consumption = metadata.get("consumption")
        generation = metadata.get("generation")
        if consumption and generation and generation > 0:
            # Calculate intensity
            intensity = consumption / generation
            return {
                "value": intensity,
                "unit": f"{metadata.get('consumption_units', 'MMBtu')} / {metadata.get('generation_units', 'MWh')}",
                "period": metadata.get("period", ""),
                "fuel_type": metadata.get("fuel_type", ""),
                "facility": metadata.get("plant_name", ""),
                "location": metadata.get("state", ""),
            }

    # Check for carbon intensity from raw_data
    if entity.raw_data:
        if "carbon_intensity" in entity.raw_data:
            return {
                "value": entity.raw_data.get("carbon_intensity"),
                "unit": "kg CO2e per unit",
                "source": entity.raw_data.get("source", ""),
            }
        if "emission_factor" in entity.raw_data:
            return {
                "value": entity.raw_data.get("emission_factor"),
                "unit": entity.raw_data.get("unit", "kg CO2e"),
                "source": entity.raw_data.get("source", ""),
            }

    return None


async def search_emission_factors(
    query: str,
    limit: int = 10,
    min_similarity: float = 0.0,
) -> list[dict]:
    """
    Search for emission factors using semantic similarity.

    Args:
        query: Natural language search query
        limit: Maximum number of results
        min_similarity: Minimum cosine similarity threshold

    Returns:
        List of results with emission factors
    """
    # Generate query embedding
    query_embedding = generate_embedding(query)

    async with get_db_context() as db:
        # Search entities
        stmt = (
            select(
                CarbonEntity,
                (1 - CarbonEntity.embedding.cosine_distance(query_embedding)).label("similarity"),
            )
            .where(CarbonEntity.embedding.is_not(None))
            .order_by(text("similarity DESC"))
            .limit(limit * 3)  # Get more results to filter
        )

        result = await db.execute(stmt)
        rows = result.all()

        # Extract emission factors
        results = []
        for entity, similarity in rows:
            if similarity >= min_similarity:
                emission_factor = extract_emission_factor(entity)

                if emission_factor:
                    results.append({
                        "entity": entity,
                        "similarity": float(similarity),
                        "emission_factor": emission_factor,
                    })

                    if len(results) >= limit:
                        break

        return results


async def search_and_display(
    query: str,
    limit: int = 10,
    min_similarity: float = 0.0,
    show_details: bool = False,
):
    """Search and display emission factors."""
    print(f"\n{'='*80}")
    print(f"Emission Factor Search: '{query}'")
    print(f"{'='*80}")
    print(f"Limit: {limit} results")
    if min_similarity > 0:
        print(f"Minimum similarity: {min_similarity}")
    print()

    results = await search_emission_factors(
        query=query,
        limit=limit,
        min_similarity=min_similarity,
    )

    if not results:
        print("No emission factors found!")
        print("\nTip: Try searching for:")
        print("  - Specific fuels: 'coal', 'natural gas', 'petroleum'")
        print("  - Processes: 'electricity generation', 'steel production'")
        print("  - Locations: 'California emissions', 'Texas power'")
        return

    print(f"Found {len(results)} emission factors:\n")

    for i, result in enumerate(results, 1):
        entity = result["entity"]
        similarity = result["similarity"]
        ef = result["emission_factor"]

        print(f"{i}. [{similarity:.3f}] {entity.name}")
        print(f"   Type: {entity.entity_type}")

        # Display emission factor
        print(f"\n   📊 EMISSION FACTOR:")
        print(f"      Value: {ef['value']:,.2f} {ef['unit']}")

        if "period" in ef and ef["period"]:
            print(f"      Period: {ef['period']}")

        if "fuel_type" in ef and ef["fuel_type"]:
            print(f"      Fuel: {ef['fuel_type']}")

        if "sector" in ef and ef["sector"]:
            print(f"      Sector: {ef['sector']}")

        if "location" in ef and ef["location"]:
            print(f"      Location: {ef['location']}")

        if "facility" in ef and ef["facility"]:
            print(f"      Facility: {ef['facility']}")

        if show_details:
            if entity.description:
                desc = entity.description[:150] + "..." if len(entity.description) > 150 else entity.description
                print(f"\n   Description: {desc}")

            if entity.category_hierarchy:
                print(f"   Categories: {' > '.join(entity.category_hierarchy[:4])}")

        print()

    logger.info(
        "emission_factor_search_complete",
        query=query,
        results_count=len(results),
        top_similarity=results[0]["similarity"] if results else 0,
    )


async def main_async(args):
    """Main async function."""
    await search_and_display(
        query=args.query,
        limit=args.limit,
        min_similarity=args.min_similarity,
        show_details=args.details,
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Search for emission factors using natural language"
    )
    parser.add_argument(
        "query",
        type=str,
        help="Search query (e.g., 'coal emissions', 'steel production')",
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)",
    )
    parser.add_argument(
        "-s", "--min-similarity",
        type=float,
        default=0.0,
        help="Minimum similarity threshold 0-1 (default: 0.0)",
    )
    parser.add_argument(
        "-d", "--details",
        action="store_true",
        help="Show detailed information for each result",
    )

    args = parser.parse_args()

    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
