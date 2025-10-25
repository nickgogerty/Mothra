"""
Add sample carbon entities to database for testing.

This script creates sample carbon entities representing common emission sources,
processes, and materials so you can test the embedding and search functionality.
"""

import asyncio
import uuid
from datetime import UTC, datetime

from mothra.db.models import CarbonEntity
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger

logger = get_logger(__name__)

# Sample carbon entities covering various industries and types
SAMPLE_ENTITIES = [
    # Energy & Electricity
    {
        "name": "Coal-fired electricity generation",
        "description": "Electricity generated from coal combustion in thermal power plants. "
        "High carbon intensity due to coal's carbon content and lower efficiency.",
        "entity_type": "process",
        "category_hierarchy": ["energy", "electricity", "fossil_fuels", "coal"],
        "geographic_scope": ["global"],
        "quality_score": 0.85,
        "custom_tags": ["electricity", "coal", "power_generation", "stationary_combustion"],
    },
    {
        "name": "Natural gas electricity generation",
        "description": "Electricity from natural gas combined cycle power plants. "
        "Lower emissions than coal but still significant carbon footprint.",
        "entity_type": "process",
        "category_hierarchy": ["energy", "electricity", "fossil_fuels", "natural_gas"],
        "geographic_scope": ["global"],
        "quality_score": 0.9,
        "custom_tags": ["electricity", "natural_gas", "power_generation", "ccgt"],
    },
    {
        "name": "Solar photovoltaic electricity",
        "description": "Electricity from solar PV panels. Very low operational emissions, "
        "most emissions from manufacturing and installation.",
        "entity_type": "process",
        "category_hierarchy": ["energy", "electricity", "renewable", "solar"],
        "geographic_scope": ["global"],
        "quality_score": 0.8,
        "custom_tags": ["electricity", "solar", "renewable", "pv"],
    },
    {
        "name": "Wind electricity generation",
        "description": "Electricity from wind turbines. Near-zero operational emissions, "
        "lifecycle emissions from turbine manufacturing.",
        "entity_type": "process",
        "category_hierarchy": ["energy", "electricity", "renewable", "wind"],
        "geographic_scope": ["global"],
        "quality_score": 0.85,
        "custom_tags": ["electricity", "wind", "renewable", "turbine"],
    },
    # Steel Production
    {
        "name": "Steel production from blast furnace",
        "description": "Primary steel production using blast furnace and basic oxygen furnace (BF-BOF). "
        "High emissions from coal use in reduction process.",
        "entity_type": "process",
        "category_hierarchy": ["industrial", "metals", "steel", "primary_production"],
        "geographic_scope": ["global"],
        "quality_score": 0.9,
        "custom_tags": ["steel", "blast_furnace", "heavy_industry", "primary_steel"],
    },
    {
        "name": "Steel production from electric arc furnace",
        "description": "Secondary steel production using electric arc furnace (EAF) with scrap metal. "
        "Lower emissions than blast furnace, depends on electricity source.",
        "entity_type": "process",
        "category_hierarchy": ["industrial", "metals", "steel", "secondary_production"],
        "geographic_scope": ["global"],
        "quality_score": 0.85,
        "custom_tags": ["steel", "eaf", "recycled_steel", "secondary_steel"],
    },
    # Cement
    {
        "name": "Portland cement production",
        "description": "Cement production from limestone calcination and fuel combustion. "
        "High process emissions from chemical reaction plus fuel combustion.",
        "entity_type": "process",
        "category_hierarchy": ["industrial", "minerals", "cement", "portland_cement"],
        "geographic_scope": ["global"],
        "quality_score": 0.9,
        "custom_tags": ["cement", "limestone", "calcination", "construction_materials"],
    },
    # Transportation
    {
        "name": "Heavy-duty diesel truck transport",
        "description": "Freight transport using heavy-duty diesel trucks. Emissions from diesel combustion, "
        "measured per tonne-kilometer.",
        "entity_type": "process",
        "category_hierarchy": ["transport", "road", "freight", "heavy_duty"],
        "geographic_scope": ["global"],
        "quality_score": 0.8,
        "custom_tags": ["transport", "trucking", "diesel", "logistics"],
    },
    {
        "name": "Container ship ocean freight",
        "description": "International ocean freight shipping in container vessels. "
        "Relatively efficient per tonne-km but uses heavy fuel oil.",
        "entity_type": "process",
        "category_hierarchy": ["transport", "shipping", "ocean", "container"],
        "geographic_scope": ["global"],
        "quality_score": 0.75,
        "custom_tags": ["shipping", "ocean", "freight", "hfo"],
    },
    {
        "name": "Air freight - long haul",
        "description": "Long-distance air cargo transport. High emissions intensity per tonne-km "
        "due to fuel consumption and altitude effects.",
        "entity_type": "process",
        "category_hierarchy": ["transport", "aviation", "freight", "long_haul"],
        "geographic_scope": ["global"],
        "quality_score": 0.8,
        "custom_tags": ["aviation", "air_freight", "cargo", "jet_fuel"],
    },
    # Materials
    {
        "name": "Aluminum production from bauxite",
        "description": "Primary aluminum production from bauxite ore through Bayer process and electrolysis. "
        "Energy-intensive with high emissions, especially if using coal power.",
        "entity_type": "material",
        "category_hierarchy": ["industrial", "metals", "aluminum", "primary_production"],
        "geographic_scope": ["global"],
        "quality_score": 0.85,
        "custom_tags": ["aluminum", "bauxite", "primary_aluminum", "electrolysis"],
    },
    {
        "name": "Recycled aluminum production",
        "description": "Aluminum from recycled scrap. Much lower emissions than primary production, "
        "only 5-10% of energy required.",
        "entity_type": "material",
        "category_hierarchy": ["industrial", "metals", "aluminum", "recycled"],
        "geographic_scope": ["global"],
        "quality_score": 0.85,
        "custom_tags": ["aluminum", "recycled", "secondary_aluminum", "circular_economy"],
    },
    {
        "name": "Plastic resin - polyethylene (PE)",
        "description": "Polyethylene plastic resin production from ethylene. Common plastic for packaging "
        "and consumer products, emissions from petrochemical feedstock and energy.",
        "entity_type": "material",
        "category_hierarchy": ["industrial", "chemicals", "plastics", "polyethylene"],
        "geographic_scope": ["global"],
        "quality_score": 0.8,
        "custom_tags": ["plastics", "polyethylene", "petrochemicals", "packaging"],
    },
    # Agriculture
    {
        "name": "Beef cattle farming",
        "description": "Beef production from cattle farming. High emissions from enteric fermentation (methane), "
        "feed production, and land use change.",
        "entity_type": "process",
        "category_hierarchy": ["agriculture", "livestock", "cattle", "beef"],
        "geographic_scope": ["global"],
        "quality_score": 0.7,
        "custom_tags": ["agriculture", "beef", "livestock", "methane", "cattle"],
    },
    {
        "name": "Rice cultivation - flooded fields",
        "description": "Rice grown in flooded paddy fields. Significant methane emissions from anaerobic "
        "decomposition in flooded conditions.",
        "entity_type": "process",
        "category_hierarchy": ["agriculture", "crops", "grains", "rice"],
        "geographic_scope": ["global"],
        "quality_score": 0.75,
        "custom_tags": ["agriculture", "rice", "paddy", "methane", "crops"],
    },
    # Chemicals
    {
        "name": "Ammonia production via Haber-Bosch",
        "description": "Ammonia synthesis from nitrogen and hydrogen using Haber-Bosch process. "
        "Energy-intensive, hydrogen often from natural gas.",
        "entity_type": "process",
        "category_hierarchy": ["industrial", "chemicals", "fertilizers", "ammonia"],
        "geographic_scope": ["global"],
        "quality_score": 0.9,
        "custom_tags": ["chemicals", "ammonia", "fertilizer", "haber_bosch"],
    },
    {
        "name": "Ethylene production via steam cracking",
        "description": "Ethylene production from steam cracking of naphtha or ethane. "
        "Key building block for plastics and chemicals.",
        "entity_type": "process",
        "category_hierarchy": ["industrial", "chemicals", "petrochemicals", "olefins"],
        "geographic_scope": ["global"],
        "quality_score": 0.85,
        "custom_tags": ["chemicals", "ethylene", "steam_cracking", "petrochemicals"],
    },
    # Buildings
    {
        "name": "Natural gas heating - residential",
        "description": "Space heating and water heating using natural gas boilers in residential buildings. "
        "Direct emissions from gas combustion.",
        "entity_type": "process",
        "category_hierarchy": ["buildings", "heating", "residential", "natural_gas"],
        "geographic_scope": ["global"],
        "quality_score": 0.85,
        "custom_tags": ["buildings", "heating", "natural_gas", "residential"],
    },
    {
        "name": "Electric heat pump heating",
        "description": "Space heating using electric heat pumps. Emissions depend on electricity grid mix, "
        "highly efficient (COP 3-4).",
        "entity_type": "process",
        "category_hierarchy": ["buildings", "heating", "residential", "electric"],
        "geographic_scope": ["global"],
        "quality_score": 0.8,
        "custom_tags": ["buildings", "heat_pump", "electric", "efficient"],
    },
    # Waste
    {
        "name": "Municipal solid waste landfill",
        "description": "Disposal of municipal solid waste in landfills. Emissions from anaerobic decomposition "
        "producing methane and CO2.",
        "entity_type": "process",
        "category_hierarchy": ["waste", "disposal", "landfill", "municipal"],
        "geographic_scope": ["global"],
        "quality_score": 0.7,
        "custom_tags": ["waste", "landfill", "methane", "municipal_waste"],
    },
    {
        "name": "Waste incineration with energy recovery",
        "description": "Waste-to-energy incineration. CO2 emissions from combustion but generates electricity, "
        "avoids landfill methane.",
        "entity_type": "process",
        "category_hierarchy": ["waste", "disposal", "incineration", "wte"],
        "geographic_scope": ["global"],
        "quality_score": 0.75,
        "custom_tags": ["waste", "incineration", "energy_recovery", "wte"],
    },
]


async def add_sample_data() -> int:
    """Add sample carbon entities to the database."""
    logger.info("adding_sample_data_starting")

    added = 0

    async with get_db_context() as db:
        for entity_data in SAMPLE_ENTITIES:
            # Create CarbonEntity
            entity = CarbonEntity(
                id=uuid.uuid4(),
                source_id="sample_data",  # Required field
                name=entity_data["name"],
                description=entity_data["description"],
                entity_type=entity_data["entity_type"],
                category_hierarchy=entity_data["category_hierarchy"],
                geographic_scope=entity_data["geographic_scope"],
                quality_score=entity_data.get("quality_score", 0.5),
                custom_tags=entity_data.get("custom_tags", []),
            )

            db.add(entity)
            added += 1

            logger.debug("sample_entity_added", name=entity.name, type=entity.entity_type)

        await db.commit()

    logger.info("sample_data_added", total=added)
    return added


async def main() -> None:
    """CLI entry point."""
    print("Adding sample carbon entities to database...")
    count = await add_sample_data()
    print(f"✅ Added {count} sample carbon entities!")
    print("\nNext steps:")
    print("1. Generate embeddings: python -m mothra.agents.embedding.vector_manager")
    print("2. Test search: python scripts/test_search.py")


if __name__ == "__main__":
    asyncio.run(main())
