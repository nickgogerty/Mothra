"""
Generate 10,000+ Sample Carbon Entities.

Creates a comprehensive dataset covering:
- Energy generation (coal, gas, nuclear, renewables)
- Industrial processes (steel, cement, chemicals, aluminum)
- Transportation (road, rail, air, sea)
- Agriculture (crops, livestock, forestry)
- Waste (landfill, incineration, recycling)
- Buildings (heating, cooling, materials)

Includes varying document sizes to test chunking:
- Short: 500-1000 characters
- Medium: 1000-2000 characters
- Long: 2000-5000 characters (requires chunking)
"""

import asyncio
import random
import uuid
from datetime import UTC, datetime

from mothra.db.models import CarbonEntity
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


# Template data for generating diverse entities
ENERGY_SOURCES = {
    "Coal": {
        "types": ["Bituminous", "Anthracite", "Lignite", "Sub-bituminous"],
        "uses": ["power generation", "steel production", "cement kilns", "industrial heating"],
        "emission_range": (800, 1200),
        "quality": (0.85, 0.95),
    },
    "Natural Gas": {
        "types": ["Pipeline", "LNG", "CNG", "Shale gas"],
        "uses": ["power generation", "heating", "industrial processes", "chemical feedstock"],
        "emission_range": (400, 550),
        "quality": (0.90, 0.95),
    },
    "Solar": {
        "types": ["Photovoltaic", "Concentrated solar power", "Solar thermal", "Thin-film"],
        "uses": ["grid electricity", "distributed generation", "water heating", "industrial process heat"],
        "emission_range": (10, 50),
        "quality": (0.80, 0.90),
    },
    "Wind": {
        "types": ["Onshore", "Offshore", "Small-scale", "Utility-scale"],
        "uses": ["grid electricity", "distributed generation", "water pumping", "hydrogen production"],
        "emission_range": (5, 30),
        "quality": (0.80, 0.90),
    },
    "Nuclear": {
        "types": ["PWR", "BWR", "CANDU", "SMR"],
        "uses": ["baseload power", "district heating", "desalination", "hydrogen production"],
        "emission_range": (5, 20),
        "quality": (0.90, 0.95),
    },
    "Hydro": {
        "types": ["Run-of-river", "Reservoir", "Pumped storage", "Small hydro"],
        "uses": ["grid electricity", "peak load", "energy storage", "irrigation"],
        "emission_range": (5, 40),
        "quality": (0.85, 0.92),
    },
}

INDUSTRIAL_PROCESSES = {
    "Steel": {
        "methods": ["Blast furnace", "Electric arc furnace", "Direct reduced iron", "Induction furnace"],
        "products": ["Hot-rolled coil", "Rebar", "Wire rod", "Structural steel"],
        "emission_range": (1500, 2500),
        "quality": (0.88, 0.95),
    },
    "Cement": {
        "methods": ["Dry process", "Wet process", "Semi-dry process", "Blended cement"],
        "products": ["Portland cement", "Blended cement", "White cement", "Specialty cement"],
        "emission_range": (700, 950),
        "quality": (0.90, 0.95),
    },
    "Aluminum": {
        "methods": ["Primary smelting", "Secondary recycling", "Bayer process", "Hall-Héroult process"],
        "products": ["Ingots", "Extrusions", "Sheet", "Castings"],
        "emission_range": (8000, 12000),
        "quality": (0.85, 0.92),
    },
    "Chemicals": {
        "methods": ["Steam cracking", "Catalytic reforming", "Haber-Bosch", "Contact process"],
        "products": ["Ammonia", "Ethylene", "Propylene", "Methanol"],
        "emission_range": (1000, 3500),
        "quality": (0.82, 0.90),
    },
}

TRANSPORT_MODES = {
    "Road": {
        "vehicle_types": ["Diesel truck", "Gasoline car", "Electric vehicle", "Hybrid bus"],
        "loads": ["Empty", "Half load", "Full load", "Overweight"],
        "emission_range": (50, 300),
        "quality": (0.80, 0.90),
    },
    "Rail": {
        "vehicle_types": ["Diesel locomotive", "Electric train", "Freight car", "High-speed rail"],
        "loads": ["Passenger", "Freight", "Mixed", "Express"],
        "emission_range": (20, 100),
        "quality": (0.85, 0.92),
    },
    "Air": {
        "vehicle_types": ["Short-haul jet", "Long-haul jet", "Turboprop", "Cargo plane"],
        "loads": ["Economy class", "Business class", "Cargo", "Mail"],
        "emission_range": (90, 400),
        "quality": (0.82, 0.90),
    },
    "Sea": {
        "vehicle_types": ["Container ship", "Bulk carrier", "Tanker", "Ferry"],
        "loads": ["Full containers", "Bulk cargo", "Liquid cargo", "Passengers"],
        "emission_range": (5, 50),
        "quality": (0.75, 0.88),
    },
}

COUNTRIES = [
    "USA", "China", "India", "Germany", "UK", "France", "Japan", "Brazil",
    "Canada", "Australia", "Mexico", "Italy", "Spain", "Netherlands", "Poland",
    "South Korea", "Sweden", "Norway", "Denmark", "Finland",
]

YEARS = list(range(2015, 2025))


def generate_long_description(category: str, subcategory: str, details: dict) -> str:
    """Generate a long, detailed description for chunking tests."""
    desc_parts = [
        f"This carbon footprint assessment covers {subcategory} within the {category} sector. ",
    ]

    # Add technical details
    if "methods" in details:
        methods = random.sample(details["methods"], min(2, len(details["methods"])))
        desc_parts.append(
            f"The production methodology includes {' and '.join(methods)}, "
            f"which are commonly used in industrial facilities worldwide. "
        )

    if "types" in details:
        types = random.sample(details["types"], min(2, len(details["types"])))
        desc_parts.append(
            f"Common variants include {' and '.join(types)}. "
        )

    # Add emission details
    emission_min, emission_max = details["emission_range"]
    avg_emission = (emission_min + emission_max) / 2
    desc_parts.append(
        f"Typical greenhouse gas emissions range from {emission_min} to {emission_max} "
        f"kg CO2e per functional unit, with an average of approximately {avg_emission:.1f} kg CO2e. "
        f"These emissions include direct combustion emissions (Scope 1), "
        f"indirect emissions from purchased electricity (Scope 2), "
        f"and relevant value chain emissions (Scope 3). "
    )

    # Add geographic context
    countries = random.sample(COUNTRIES, 3)
    desc_parts.append(
        f"Geographic variations exist across regions, with significant operations in "
        f"{', '.join(countries[:-1])}, and {countries[-1]}. "
        f"Regional differences stem from fuel mix, grid carbon intensity, "
        f"regulatory requirements, and technology adoption rates. "
    )

    # Add temporal context
    year = random.choice(YEARS)
    desc_parts.append(
        f"This data represents conditions as of {year}, "
        f"reflecting the state of technology and practices at that time. "
        f"Carbon intensity has evolved over the past decade due to "
        f"efficiency improvements, fuel switching, and renewable energy integration. "
    )

    # Add lifecycle information
    desc_parts.append(
        "The lifecycle assessment includes raw material extraction, "
        "transportation to facility, processing and manufacturing, "
        "product distribution, use phase, and end-of-life treatment. "
        "Embodied carbon in infrastructure and equipment is amortized "
        "over the expected operational lifetime. "
    )

    # Add uncertainty and data quality
    quality_min, quality_max = details["quality"]
    avg_quality = (quality_min + quality_max) / 2
    desc_parts.append(
        f"Data quality score is {avg_quality:.2f} based on temporal correlation, "
        f"geographic correlation, technological correlation, completeness, "
        f"and reliability of the underlying data sources. "
        f"Primary data from facility measurements provides the highest quality, "
        f"supplemented by industry averages and literature values where necessary. "
    )

    # Add regulatory context
    desc_parts.append(
        "Regulatory frameworks including the EU Emissions Trading System, "
        "California Cap-and-Trade, and voluntary standards like the "
        "GHG Protocol and ISO 14064 govern measurement and reporting. "
        "Verification by third-party auditors ensures data accuracy and compliance. "
    )

    return "".join(desc_parts)


async def generate_entities(total: int = 10000, batch_size: int = 100) -> int:
    """Generate sample entities in batches."""
    logger.info("generation_started", total=total)

    added = 0
    categories = list(ENERGY_SOURCES.keys()) + list(INDUSTRIAL_PROCESSES.keys()) + list(TRANSPORT_MODES.keys())

    # Distribute across categories
    per_category = total // len(categories)

    async with get_db_context() as db:
        for category_name in categories:
            # Determine category type and details
            if category_name in ENERGY_SOURCES:
                category_type = "energy"
                details = ENERGY_SOURCES[category_name]
                hierarchy_base = ["energy", "generation"]
            elif category_name in INDUSTRIAL_PROCESSES:
                category_type = "industrial"
                details = INDUSTRIAL_PROCESSES[category_name]
                hierarchy_base = ["industrial", "manufacturing"]
            else:
                category_type = "transport"
                details = TRANSPORT_MODES[category_name]
                hierarchy_base = ["transport", "logistics"]

            # Generate entities for this category
            for i in range(per_category):
                # Vary description length
                length_type = random.choices(
                    ["short", "medium", "long"],
                    weights=[0.3, 0.4, 0.3]  # 30% short, 40% medium, 30% long
                )[0]

                if length_type == "long":
                    description = generate_long_description(category_type, category_name, details)
                elif length_type == "medium":
                    description = generate_long_description(category_type, category_name, details)[:1500]
                else:
                    description = generate_long_description(category_type, category_name, details)[:800]

                # Generate name
                variant = random.choice(details.get("types", details.get("methods", details.get("vehicle_types", ["Standard"]))))
                year = random.choice(YEARS)
                country = random.choice(COUNTRIES)
                name = f"{category_name} {variant} - {country} ({year})"

                # Generate category hierarchy
                category_hierarchy = hierarchy_base + [category_name.lower(), variant.lower().replace(" ", "_")]

                # Generate emissions value
                emission_min, emission_max = details["emission_range"]
                emission_value = random.uniform(emission_min, emission_max)

                # Generate quality score
                quality_min, quality_max = details["quality"]
                quality_score = random.uniform(quality_min, quality_max)

                # Create entity
                entity = CarbonEntity(
                    id=uuid.uuid4(),
                    source_id="generated_samples_10k",
                    name=name,
                    description=description,
                    entity_type="process",
                    category_hierarchy=category_hierarchy,
                    geographic_scope=[country, "Global"],
                    quality_score=quality_score,
                    custom_tags=[
                        category_type,
                        category_name.lower(),
                        variant.lower().replace(" ", "_"),
                        country.lower(),
                        f"year_{year}",
                    ],
                    extra_metadata={
                        "emission_value": emission_value,
                        "unit": "kg CO2e",
                        "year": year,
                        "variant": variant,
                        "length_type": length_type,
                    },
                )

                db.add(entity)
                added += 1

                # Commit in batches
                if added % batch_size == 0:
                    await db.commit()
                    logger.info("batch_committed", added=added, total=total)
                    print(f"Progress: {added}/{total} ({added/total*100:.1f}%)")

        # Commit remaining
        await db.commit()

    logger.info("generation_complete", total=added)
    return added


async def main():
    """Generate 10,000 sample entities."""
    print("=" * 80)
    print("Generating 10,000 Sample Carbon Entities")
    print("=" * 80)
    print("\nThis will create diverse entities with varying document sizes:")
    print("- 30% short (500-1000 chars)")
    print("- 40% medium (1000-2000 chars)")
    print("- 30% long (2000-5000 chars, requires chunking)")
    print("\nCategories covered:")
    print("- Energy generation (Coal, Gas, Solar, Wind, Nuclear, Hydro)")
    print("- Industrial processes (Steel, Cement, Aluminum, Chemicals)")
    print("- Transportation (Road, Rail, Air, Sea)")
    print("\nThis may take 5-10 minutes...")
    print()

    start_time = datetime.now(UTC)

    count = await generate_entities(total=10000, batch_size=100)

    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()

    print("\n" + "=" * 80)
    print("✅ Generation Complete!")
    print("=" * 80)
    print(f"\nEntities created: {count:,}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Rate: {count/duration:.1f} entities/second")
    print("\nNext steps:")
    print("1. Run chunking and embedding: python scripts/chunk_and_embed_all.py")
    print("2. Test search with large dataset: python scripts/test_search.py")


if __name__ == "__main__":
    asyncio.run(main())
