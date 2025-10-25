"""
UK DEFRA Conversion Factors Parser.

Parses emission factors from UK DEFRA's annual conversion factors database.
Source: https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting

Published annually as Excel files with comprehensive emission factors for:
- Fuels
- Electricity
- Transport (road, rail, air, sea)
- Refrigerants
- Water
- Waste
- Material use
- And more

Excel structure typically has multiple sheets with tables of emission factors.
"""

import json
from typing import Any

from mothra.agents.parser.base_parser import BaseParser
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class UKDEFRAParser(BaseParser):
    """Parser for UK DEFRA conversion factors."""

    # Sheet/category to hierarchy mapping
    CATEGORY_MAP = {
        "Fuels": ["energy", "fuels", "combustion"],
        "UK electricity": ["energy", "electricity", "grid"],
        "Transmission and distribution": ["energy", "electricity", "transmission"],
        "Passenger vehicles": ["transport", "road", "passenger"],
        "Delivery vehicles": ["transport", "road", "freight"],
        "Road": ["transport", "road", "vehicle"],
        "Rail": ["transport", "rail", "passenger"],
        "Air": ["transport", "aviation", "passenger"],
        "Sea": ["transport", "shipping", "freight"],
        "Refrigerants": ["industrial", "refrigerants", "cooling"],
        "Water supply": ["utilities", "water", "supply"],
        "Water treatment": ["waste", "water", "treatment"],
        "Waste disposal": ["waste", "disposal", "treatment"],
        "Material use": ["industrial", "materials", "manufacturing"],
        "Freighting goods": ["transport", "freight", "logistics"],
    }

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse UK DEFRA conversion factors.

        Args:
            data: Raw data (JSON dict for pre-processed Excel, or raw bytes/string)

        Returns:
            List of entity dictionaries for emission factors
        """
        # If data is already structured (pre-processed Excel to JSON)
        if isinstance(data, dict):
            return await self._parse_structured(data)
        elif isinstance(data, list):
            return await self._parse_list(data)
        else:
            logger.warning("unsupported_defra_format", data_type=type(data))
            return []

    async def _parse_structured(self, data: dict) -> list[dict[str, Any]]:
        """Parse structured JSON from processed Excel file."""
        entities = []

        # Iterate through sheets/categories
        for sheet_name, records in data.items():
            if not isinstance(records, list):
                continue

            for record in records:
                entity = self._create_emission_factor_entity(record, sheet_name)
                if entity:
                    entities.append(entity)

        logger.info(
            "uk_defra_parsed",
            total_entities=len(entities),
            sheets=len(data),
        )

        return entities

    async def _parse_list(self, data: list) -> list[dict[str, Any]]:
        """Parse list of emission factor records."""
        entities = []

        for record in data:
            # Try to determine category from record
            category = record.get("category") or record.get("sheet") or "Other"
            entity = self._create_emission_factor_entity(record, category)
            if entity:
                entities.append(entity)

        logger.info(
            "uk_defra_list_parsed",
            total_entities=len(entities),
        )

        return entities

    def _create_emission_factor_entity(
        self, record: dict[str, Any], category: str
    ) -> dict[str, Any] | None:
        """Create entity from emission factor record."""
        # Extract fields with flexible key names
        activity = (record.get("activity") or record.get("Activity") or
                   record.get("Fuel") or record.get("fuel") or
                   record.get("Type") or record.get("type") or "")

        # Emission factor fields
        co2 = record.get("kg CO2e") or record.get("kgCO2e") or record.get("co2e")
        unit = (record.get("Unit") or record.get("unit") or
               record.get("Per Unit") or "")

        # Additional GHG breakdown
        co2_only = record.get("kg CO2") or record.get("kgCO2")
        ch4 = record.get("kg CH4") or record.get("kgCH4")
        n2o = record.get("kg N2O") or record.get("kgN2O")

        # Scope information (for electricity/energy)
        scope = record.get("Scope") or record.get("scope") or ""

        # Year of data
        year = record.get("Year") or record.get("year") or "2023"

        # Skip if no emission factor
        if not co2:
            return None

        try:
            co2e_value = float(co2)
        except (ValueError, TypeError):
            return None

        # Get category hierarchy
        category_hierarchy = self.CATEGORY_MAP.get(
            category,
            ["energy", "emission_factors", "uk"]
        )

        # Build name
        name = f"UK DEFRA: {activity} ({category})"

        # Build description
        description = (
            f"UK DEFRA emission factor for {activity} in {category} category. "
            f"Factor: {co2e_value} kg CO2e per {unit}. "
        )

        if scope:
            description += f"Scope: {scope}. "

        if co2_only:
            description += f"Breakdown - CO2: {co2_only}, "
            if ch4:
                description += f"CH4: {ch4}, "
            if n2o:
                description += f"N2O: {n2o}. "

        description += f"Reference year: {year}. Source: UK DEFRA."

        # Quality score - DEFRA data is high quality
        quality_score = 0.92

        # Custom tags
        custom_tags = ["defra", "uk", "emission_factor", "conversion_factor"]
        if category:
            custom_tags.append(category.lower().replace(" ", "_"))
        if activity:
            # Add first word of activity as tag
            first_word = activity.split()[0].lower() if activity else ""
            if first_word and len(first_word) > 2:
                custom_tags.append(first_word)

        # Create entity
        entity = self.create_entity_dict(
            name=name,
            description=description,
            entity_type="process",
            category_hierarchy=category_hierarchy,
            geographic_scope=["UK"],
            quality_score=quality_score,
            custom_tags=custom_tags,
            # Metadata
            activity=activity,
            category=category,
            emission_factor_co2e=co2e_value,
            emission_factor_co2=co2_only,
            emission_factor_ch4=ch4,
            emission_factor_n2o=n2o,
            unit=unit,
            scope=scope,
            year=year,
            data_source="UK DEFRA",
            raw_data=record,
        )

        return entity
