"""
Test All Carbon Data Parsers.

This script tests all implemented parsers with sample data to demonstrate
their functionality and validate the parsing logic.
"""

import asyncio
import uuid

from mothra.agents.parser import (
    UKCarbonIntensityParser,
    EPAGHGRPParser,
    EUETSParser,
    IPCCEmissionFactorParser,
    UKDEFRAParser,
    EPDInternationalParser,
)
from mothra.db.models import DataSource, CarbonEntity
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


# Sample data for each parser
SAMPLE_DATA = {
    "uk_carbon_intensity": {
        "data": [
            {
                "from": "2024-10-25T16:00Z",
                "to": "2024-10-25T16:30Z",
                "intensity": {
                    "forecast": 195,
                    "actual": 200,
                    "index": "moderate"
                }
            },
            {
                "from": "2024-10-25T16:30Z",
                "to": "2024-10-25T17:00Z",
                "intensity": {
                    "forecast": 185,
                    "actual": 190,
                    "index": "moderate"
                }
            }
        ]
    },
    "epa_ghgrp": [
        {
            "FACILITY_NAME": "Example Coal Power Plant",
            "FACILITY_ID": "1001234",
            "REPORTING_YEAR": "2022",
            "STATE": "TX",
            "CITY": "Houston",
            "ZIP": "77002",
            "LATITUDE": "29.7604",
            "LONGITUDE": "-95.3698",
            "INDUSTRY_TYPE": "Power Plants",
            "GHGQUANTITY": "5500000",
            "GHG_NAME": "Carbon Dioxide",
            "UNIT": "Metric Tons CO2e"
        },
        {
            "FACILITY_NAME": "Natural Gas Processing Facility",
            "FACILITY_ID": "1001235",
            "REPORTING_YEAR": "2022",
            "STATE": "PA",
            "CITY": "Pittsburgh",
            "INDUSTRY_TYPE": "Petroleum and Natural Gas Systems",
            "GHGQUANTITY": "850000",
            "GHG_NAME": "Methane",
            "UNIT": "Metric Tons CO2e"
        }
    ],
    "eu_ets": {
        "installations": [
            {
                "account_id": "EU-12345",
                "name": "Example Steel Mill",
                "permit_id": "DE-123-456",
                "country": "DE",
                "activity_type": "Production of pig iron or steel",
                "year": "2022",
                "emissions": "1500000",
                "unit": "tCO2e"
            },
            {
                "account_id": "EU-12346",
                "name": "Example Cement Plant",
                "permit_id": "FR-789-012",
                "country": "FR",
                "activity_type": "Production of cement clinker",
                "year": "2022",
                "emissions": "980000",
                "unit": "tCO2e"
            }
        ]
    },
    "ipcc_emission_factors": [
        {
            "sector": "Energy - Combustion",
            "fuel_material": "Natural Gas",
            "factor": "56.1",
            "unit": "kg CO2/GJ",
            "uncertainty": "±5%",
            "reference": "IPCC 2006"
        },
        {
            "sector": "Agriculture - Enteric Fermentation",
            "fuel_material": "Dairy Cattle",
            "factor": "117",
            "unit": "kg CH4/head/yr",
            "uncertainty": "±20%",
            "reference": "IPCC 2019 Refinement"
        },
        {
            "sector": "Industrial Processes - Cement",
            "fuel_material": "Cement Clinker",
            "factor": "525",
            "unit": "kg CO2/tonne clinker",
            "uncertainty": "±10%",
            "reference": "IPCC 2006"
        }
    ],
    "uk_defra": {
        "Fuels": [
            {
                "activity": "Natural gas (100% mineral blend)",
                "kg CO2e": 0.18316,
                "kg CO2": 0.18254,
                "kg CH4": 0.00004,
                "kg N2O": 0.00002,
                "unit": "kWh",
                "year": "2023"
            },
            {
                "activity": "Diesel (average biofuel blend)",
                "kg CO2e": 3.161,
                "kg CO2": 3.150,
                "kg CH4": 0.0001,
                "kg N2O": 0.0002,
                "unit": "litre",
                "year": "2023"
            }
        ],
        "UK electricity": [
            {
                "activity": "UK electricity",
                "kg CO2e": 0.193,
                "kg CO2": 0.192,
                "unit": "kWh",
                "scope": "Scope 2",
                "year": "2023"
            }
        ],
        "Road": [
            {
                "activity": "Passenger car (medium, diesel)",
                "kg CO2e": 0.16182,
                "kg CO2": 0.16120,
                "unit": "km",
                "year": "2023"
            }
        ]
    },
    "epd_international": [
        {
            "product_name": "Concrete C30/37",
            "manufacturer": "Example Cement Company",
            "epd_number": "S-P-12345",
            "valid_until": "2025-12-31",
            "declared_unit": "1 m³",
            "gwp_total": "350",
            "gwp_a1_a3": "320",
            "gwp_unit": "kg CO2e",
            "product_category": "Concrete",
            "geography": "Germany"
        },
        {
            "product_name": "Steel rebar (reinforcing steel)",
            "manufacturer": "Global Steel Corp",
            "epd_number": "S-P-67890",
            "valid_until": "2026-06-30",
            "declared_unit": "1 tonne",
            "gwp_total": "2100",
            "gwp_a1_a3": "2050",
            "gwp_unit": "kg CO2e",
            "product_category": "Steel",
            "geography": "Europe"
        },
        {
            "product_name": "Mineral wool insulation",
            "manufacturer": "Insulation Industries",
            "epd_number": "S-P-11223",
            "valid_until": "2025-09-15",
            "declared_unit": "1 m²",
            "gwp_total": "12.5",
            "gwp_a1_a3": "11.8",
            "gwp_unit": "kg CO2e",
            "product_category": "Insulation",
            "geography": "Nordic countries"
        }
    ]
}


async def create_mock_source(name: str, url: str, source_type: str) -> DataSource:
    """Create or get mock data source."""
    async with get_db_context() as db:
        from sqlalchemy import select
        stmt = select(DataSource).where(DataSource.name == name)
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()

        if not source:
            source = DataSource(
                name=name,
                url=url,
                source_type=source_type,
                category="government",
                priority="high",
                access_method="rest",
                auth_required=False,
                status="active",
            )
            db.add(source)
            await db.commit()

        return source


async def test_parser(parser_name: str, parser_class: type, sample_data: any, source: DataSource):
    """Test a single parser."""
    print(f"\n{'=' * 80}")
    print(f"Testing {parser_name}")
    print('=' * 80)

    # Create parser
    parser = parser_class(source)

    # Parse data
    entities = await parser.parse_and_validate(sample_data)

    print(f"✅ Parsed {len(entities)} entities")

    # Display first few entities
    for i, entity in enumerate(entities[:3], 1):  # Show first 3
        print(f"\n  Entity {i}:")
        print(f"  - Name: {entity['name'][:80]}")
        print(f"  - Type: {entity['entity_type']}")
        print(f"  - Category: {' > '.join(entity['category_hierarchy'])}")
        print(f"  - Geographic Scope: {', '.join(entity['geographic_scope'])}")
        print(f"  - Quality Score: {entity['quality_score']}")
        print(f"  - Tags: {', '.join(entity['custom_tags'][:5])}")

    if len(entities) > 3:
        print(f"\n  ... and {len(entities) - 3} more entities")

    # Save to database
    async with get_db_context() as db:
        for entity_dict in entities:
            entity = CarbonEntity(**entity_dict)
            db.add(entity)
        await db.commit()

    print(f"\n✅ Saved {len(entities)} entities to database")

    return len(entities)


async def main():
    """Run all parser tests."""
    print("=" * 80)
    print("MOTHRA Parser Test Suite")
    print("=" * 80)
    print("\nTesting all implemented parsers with sample data...\n")

    total_entities = 0

    # Test 1: UK Carbon Intensity
    source1 = await create_mock_source(
        "UK Carbon Intensity API",
        "https://api.carbonintensity.org.uk",
        "api"
    )
    count1 = await test_parser(
        "UK Carbon Intensity Parser",
        UKCarbonIntensityParser,
        SAMPLE_DATA["uk_carbon_intensity"],
        source1
    )
    total_entities += count1

    # Test 2: EPA GHGRP
    source2 = await create_mock_source(
        "EPA GHGRP",
        "https://www.epa.gov/ghgreporting",
        "api"
    )
    count2 = await test_parser(
        "EPA GHGRP Parser",
        EPAGHGRPParser,
        SAMPLE_DATA["epa_ghgrp"],
        source2
    )
    total_entities += count2

    # Test 3: EU ETS
    source3 = await create_mock_source(
        "EU ETS",
        "https://ec.europa.eu/clima/ets",
        "api"
    )
    count3 = await test_parser(
        "EU ETS Parser",
        EUETSParser,
        SAMPLE_DATA["eu_ets"],
        source3
    )
    total_entities += count3

    # Test 4: IPCC Emission Factors
    source4 = await create_mock_source(
        "IPCC EFDB",
        "https://www.ipcc-nggip.iges.or.jp/EFDB",
        "web_scrape"
    )
    count4 = await test_parser(
        "IPCC Emission Factor Parser",
        IPCCEmissionFactorParser,
        SAMPLE_DATA["ipcc_emission_factors"],
        source4
    )
    total_entities += count4

    # Test 5: UK DEFRA
    source5 = await create_mock_source(
        "UK DEFRA Conversion Factors",
        "https://www.gov.uk/ghg-conversion-factors",
        "document"
    )
    count5 = await test_parser(
        "UK DEFRA Parser",
        UKDEFRAParser,
        SAMPLE_DATA["uk_defra"],
        source5
    )
    total_entities += count5

    # Test 6: EPD International
    source6 = await create_mock_source(
        "International EPD System",
        "https://www.environdec.com",
        "web_scrape"
    )
    count6 = await test_parser(
        "EPD International Parser",
        EPDInternationalParser,
        SAMPLE_DATA["epd_international"],
        source6
    )
    total_entities += count6

    # Summary
    print("\n" + "=" * 80)
    print("✅ All Parser Tests Complete!")
    print("=" * 80)
    print(f"\nTotal entities parsed: {total_entities}")
    print(f"Parsers tested: 6")
    print("\nData sources covered:")
    print("  - UK Carbon Intensity (real-time grid data)")
    print("  - EPA GHGRP (US facility emissions)")
    print("  - EU ETS (EU verified emissions)")
    print("  - IPCC Emission Factors (global factors)")
    print("  - UK DEFRA Conversion Factors (UK emission factors)")
    print("  - International EPD System (product carbon footprints)")
    print("\nNext steps:")
    print("1. Generate embeddings: python -m mothra.agents.embedding.vector_manager")
    print("2. Search the data: python scripts/test_search.py")
    print("   Try queries like:")
    print("   - 'steel production emissions'")
    print("   - 'electricity grid carbon intensity'")
    print("   - 'concrete carbon footprint'")
    print("   - 'natural gas emission factor'")


if __name__ == "__main__":
    asyncio.run(main())
