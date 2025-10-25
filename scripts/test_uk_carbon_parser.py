"""
Test UK Carbon Intensity Parser with real API data.

This script fetches current carbon intensity data from the UK API
and tests the parser to ensure it correctly extracts carbon entities.
"""

import asyncio
import aiohttp

from mothra.agents.parser.uk_carbon_intensity_parser import UKCarbonIntensityParser
from mothra.db.models import CarbonEntity, DataSource
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger

logger = get_logger(__name__)

UK_API_URL = "https://api.carbonintensity.org.uk/intensity"


async def fetch_uk_carbon_data() -> dict:
    """Fetch current carbon intensity from UK API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(UK_API_URL) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"API request failed with status {response.status}")


async def test_parser():
    """Test the UK Carbon Intensity parser."""
    print("=" * 80)
    print("UK Carbon Intensity Parser Test")
    print("=" * 80)

    # Fetch real data
    print("\n1. Fetching current UK carbon intensity data...")
    try:
        api_data = await fetch_uk_carbon_data()
        print(f"✅ Fetched data successfully")
        print(f"   API Response: {api_data}")
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        return

    # Create mock DataSource
    print("\n2. Creating mock DataSource...")
    async with get_db_context() as db:
        # Check if source already exists
        from sqlalchemy import select
        stmt = select(DataSource).where(DataSource.name == "UK Carbon Intensity API")
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()

        if not source:
            source = DataSource(
                name="UK Carbon Intensity API",
                url=UK_API_URL,
                source_type="api",
                category="government",
                priority="high",
                access_method="rest",
                auth_required=False,
                rate_limit=3600,
                update_frequency="realtime",
                data_format="json",
                estimated_size_gb=2.0,
                status="active",
            )
            db.add(source)
            await db.commit()
            print(f"✅ Created new DataSource: {source.name}")
        else:
            print(f"✅ Using existing DataSource: {source.name}")

    # Test parser
    print("\n3. Testing parser...")
    parser = UKCarbonIntensityParser(source)

    entities = await parser.parse_and_validate(api_data)

    print(f"✅ Parser extracted {len(entities)} entities")

    # Display parsed entities
    print("\n4. Parsed Entities:")
    for i, entity in enumerate(entities, 1):
        print(f"\n   Entity {i}:")
        print(f"   - Name: {entity['name']}")
        print(f"   - Type: {entity['entity_type']}")
        print(f"   - Description: {entity['description'][:100]}...")
        print(f"   - Quality Score: {entity['quality_score']}")
        print(f"   - Geographic Scope: {entity['geographic_scope']}")
        print(f"   - Tags: {entity['custom_tags']}")

    # Save to database
    print("\n5. Saving entities to database...")
    async with get_db_context() as db:
        saved_count = 0
        for entity_dict in entities:
            # Create CarbonEntity
            entity = CarbonEntity(**entity_dict)
            db.add(entity)
            saved_count += 1

        await db.commit()
        print(f"✅ Saved {saved_count} entities to database")

    print("\n" + "=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Generate embeddings: python -m mothra.agents.embedding.vector_manager")
    print("2. Search for UK grid data: python scripts/test_search.py")
    print("   Try queries like: 'UK electricity grid carbon intensity'")


if __name__ == "__main__":
    asyncio.run(test_parser())
