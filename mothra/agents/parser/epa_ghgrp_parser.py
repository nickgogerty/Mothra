"""
EPA GHGRP (Greenhouse Gas Reporting Program) Parser.

Parses facility-level greenhouse gas emissions data from EPA's GHGRP API.
API Documentation: https://www.epa.gov/ghgreporting/data-sets
Data Portal: https://enviro.epa.gov/enviro/efservice/

Example API response structure:
[
  {
    "FACILITY_NAME": "Example Power Plant",
    "FACILITY_ID": "1234567",
    "REPORTING_YEAR": "2022",
    "STATE": "TX",
    "CITY": "Houston",
    "ZIP": "77002",
    "LATITUDE": "29.7604",
    "LONGITUDE": "-95.3698",
    "INDUSTRY_TYPE": "Power Plants",
    "GHGQUANTITY": "5000000",
    "GHG_NAME": "Carbon Dioxide",
    "UNIT": "Metric Tons CO2e"
  }
]
"""

import json
from typing import Any

from mothra.agents.parser.base_parser import BaseParser
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class EPAGHGRPParser(BaseParser):
    """Parser for EPA GHGRP facility emissions data."""

    # Industry type to category mapping
    INDUSTRY_CATEGORIES = {
        "Power Plants": ["energy", "electricity", "power_generation"],
        "Petroleum and Natural Gas Systems": ["energy", "fossil_fuels", "oil_gas"],
        "Refineries": ["industrial", "refining", "petroleum"],
        "Chemicals": ["industrial", "chemicals", "manufacturing"],
        "Waste": ["waste", "landfill", "disposal"],
        "Metals": ["industrial", "metals", "manufacturing"],
        "Pulp and Paper": ["industrial", "paper", "manufacturing"],
        "Cement Production": ["industrial", "cement", "construction_materials"],
        "Lime Manufacturing": ["industrial", "lime", "construction_materials"],
        "Glass Production": ["industrial", "glass", "manufacturing"],
        "Iron and Steel": ["industrial", "steel", "metals"],
        "Ammonia Manufacturing": ["industrial", "chemicals", "fertilizer"],
    }

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse EPA GHGRP API response.

        Args:
            data: Raw API response (JSON string, bytes, or list)

        Returns:
            List of entity dictionaries for facility emissions
        """
        # Parse JSON if needed
        if isinstance(data, (str, bytes)):
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            json_data = json.loads(data)
        else:
            json_data = data

        # Handle both list and dict responses
        if isinstance(json_data, dict):
            records = json_data.get("data", [])
        else:
            records = json_data

        entities = []

        for record in records:
            # Extract facility information
            facility_name = record.get("FACILITY_NAME", "Unknown Facility")
            facility_id = record.get("FACILITY_ID", "")
            reporting_year = record.get("REPORTING_YEAR", "")
            state = record.get("STATE", "")
            city = record.get("CITY", "")
            zip_code = record.get("ZIP", "")
            latitude = record.get("LATITUDE", "")
            longitude = record.get("LONGITUDE", "")
            industry_type = record.get("INDUSTRY_TYPE", "Unknown")

            # Extract emissions data
            ghg_quantity = record.get("GHGQUANTITY") or record.get("GHG_QUANTITY")
            ghg_name = record.get("GHG_NAME", "")
            unit = record.get("UNIT", "Metric Tons CO2e")

            # Skip if no emissions data
            if not ghg_quantity:
                continue

            try:
                emissions_value = float(ghg_quantity)
            except (ValueError, TypeError):
                continue

            # Get category hierarchy for industry type
            category_hierarchy = self.INDUSTRY_CATEGORIES.get(
                industry_type,
                ["industrial", "other", "manufacturing"]
            )

            # Build geographic scope
            geographic_scope = ["USA"]
            if state:
                geographic_scope.append(f"USA-{state}")

            # Build description
            description = (
                f"{facility_name} in {city}, {state} reported {emissions_value:,.0f} {unit} "
                f"of {ghg_name} emissions for year {reporting_year}. "
                f"Industry: {industry_type}. EPA Facility ID: {facility_id}."
            )

            # Quality score based on completeness
            quality_score = 0.9  # EPA data is high quality
            if latitude and longitude:
                quality_score = 0.95  # Even better if geocoded

            # Create entity name
            entity_name = f"{facility_name} - {ghg_name} Emissions ({reporting_year})"

            # Build custom tags
            custom_tags = ["epa", "ghgrp", "facility_emissions", "usa"]
            if ghg_name:
                custom_tags.append(ghg_name.lower().replace(" ", "_"))
            if industry_type:
                custom_tags.append(industry_type.lower().replace(" ", "_"))
            if state:
                custom_tags.append(state.lower())

            # Create entity
            entity = self.create_entity_dict(
                name=entity_name,
                description=description,
                entity_type="process",
                category_hierarchy=category_hierarchy,
                geographic_scope=geographic_scope,
                quality_score=quality_score,
                custom_tags=custom_tags,
                # Metadata fields
                facility_id=facility_id,
                facility_name=facility_name,
                reporting_year=reporting_year,
                city=city,
                state=state,
                zip_code=zip_code,
                latitude=latitude,
                longitude=longitude,
                industry_type=industry_type,
                ghg_name=ghg_name,
                emissions_value=emissions_value,
                unit=unit,
                data_source="EPA GHGRP",
                raw_data=record,
            )

            entities.append(entity)

        logger.info(
            "epa_ghgrp_parsed",
            total_entities=len(entities),
            source=self.source.name,
        )

        return entities
