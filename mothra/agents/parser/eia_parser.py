"""
EIA (Energy Information Administration) Parser.

Parses energy and emissions data from EIA's Open Data API v2.
API Documentation: https://www.eia.gov/opendata/documentation.php

Supported endpoints:
1. Facility Fuel Data - Power plant emissions and fuel consumption
2. CO2 Emissions Aggregates - State-level emissions by sector and fuel
3. Electricity Generation - State and regional generation data

Example facility fuel response:
{
    "plantCode": 55,
    "plantName": "Plants",
    "stateid": "CA",
    "county": "Los Angeles",
    "sector": "Electric Utility",
    "fuelType": "Coal",
    "consumption": 12345.6,
    "consumptionUnits": "MMBtu",
    "generation": 1234,
    "generationUnits": "MWh",
    "period": "2023"
}

Example CO2 emissions response:
{
    "stateId": "CA",
    "sectorId": "ELE",
    "fuelId": "COW",
    "value": 12345678.9,
    "units": "million metric tons",
    "period": "2023"
}
"""

import json
from typing import Any

from mothra.agents.parser.base_parser import BaseParser
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class EIAParser(BaseParser):
    """Parser for EIA energy and emissions data."""

    # Sector ID to category mapping
    SECTOR_CATEGORIES = {
        "ELE": ["energy", "electricity", "power_sector"],
        "RES": ["energy", "residential", "buildings"],
        "COM": ["energy", "commercial", "buildings"],
        "IND": ["energy", "industrial", "manufacturing"],
        "TRA": ["energy", "transportation", "mobility"],
        "TT": ["energy", "total", "all_sectors"],
    }

    # Fuel type to category mapping
    FUEL_CATEGORIES = {
        "COW": ["energy", "coal", "fossil_fuel"],
        "NG": ["energy", "natural_gas", "fossil_fuel"],
        "PET": ["energy", "petroleum", "fossil_fuel"],
        "NUC": ["energy", "nuclear", "zero_carbon"],
        "HYC": ["energy", "hydroelectric", "renewable"],
        "WND": ["energy", "wind", "renewable"],
        "SUN": ["energy", "solar", "renewable"],
        "GEO": ["energy", "geothermal", "renewable"],
        "BIO": ["energy", "biomass", "renewable"],
        "OTH": ["energy", "other", "mixed"],
    }

    # State code to full name mapping (abbreviated)
    STATE_NAMES = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
        "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
        "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
        "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
        "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
        "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
        "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
        "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
        "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
        "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
        "US": "United States",
    }

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse EIA API response.

        Args:
            data: Raw API response (JSON string, bytes, dict, or list)

        Returns:
            List of entity dictionaries for emissions/energy data
        """
        # Parse JSON if needed
        if isinstance(data, (str, bytes)):
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            json_data = json.loads(data)
        else:
            json_data = data

        # Handle dict or list responses
        if isinstance(json_data, dict):
            # Try to extract records from response structure
            records = json_data.get("response", {}).get("data", [])
            if not records:
                records = json_data.get("data", [])
        elif isinstance(json_data, list):
            records = json_data
        else:
            logger.warning(
                "eia_unexpected_format",
                data_type=type(json_data).__name__,
            )
            return []

        entities = []

        for record in records:
            # Determine record type based on fields
            if self._is_facility_record(record):
                entity = self._parse_facility_record(record)
            elif self._is_emissions_aggregate_record(record):
                entity = self._parse_emissions_aggregate_record(record)
            elif self._is_generation_record(record):
                entity = self._parse_generation_record(record)
            else:
                # Generic parsing for unknown formats
                entity = self._parse_generic_record(record)

            if entity:
                entities.append(entity)

        logger.info(
            "eia_parsed",
            total_entities=len(entities),
            total_records=len(records),
            source=self.source.name,
        )

        return entities

    def _is_facility_record(self, record: dict[str, Any]) -> bool:
        """Check if record is facility fuel data."""
        return "plantCode" in record or "plant-code" in record or "facilityId" in record

    def _is_emissions_aggregate_record(self, record: dict[str, Any]) -> bool:
        """Check if record is CO2 emissions aggregate."""
        return ("stateId" in record or "stateid" in record) and (
            "sectorId" in record or "sectorid" in record
        )

    def _is_generation_record(self, record: dict[str, Any]) -> bool:
        """Check if record is electricity generation data."""
        return "generation" in record and "generationUnits" in record

    def _parse_facility_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Parse facility fuel/emissions record."""
        # Extract fields (handle different case conventions)
        plant_code = record.get("plantCode") or record.get("plant-code") or record.get("facilityId")
        plant_name = record.get("plantName") or record.get("plant-name") or f"Plant {plant_code}"
        state_id = (record.get("stateid") or record.get("stateId") or "").upper()
        county = record.get("county") or ""
        sector = record.get("sector") or record.get("sectorName") or ""
        fuel_type = record.get("fuelType") or record.get("fuel-type") or ""

        # Emissions/consumption data
        consumption = record.get("consumption") or record.get("fuelConsumption")
        consumption_units = record.get("consumptionUnits") or record.get("consumption-units") or "MMBtu"
        generation = record.get("generation") or record.get("netGeneration")
        generation_units = record.get("generationUnits") or record.get("generation-units") or "MWh"

        period = record.get("period") or ""

        # Skip if no meaningful data
        if not plant_code and not plant_name:
            return None

        # Build name and description
        entity_name = f"{plant_name} - {fuel_type or 'Energy'} ({period or 'Unknown Year'})"

        description_parts = [f"Power plant facility: {plant_name}"]
        if state_id:
            state_name = self.STATE_NAMES.get(state_id, state_id)
            description_parts.append(f"Location: {state_name}")
        if county:
            description_parts.append(f"County: {county}")
        if sector:
            description_parts.append(f"Sector: {sector}")
        if fuel_type:
            description_parts.append(f"Fuel Type: {fuel_type}")
        if consumption:
            description_parts.append(f"Consumption: {consumption:,.1f} {consumption_units}")
        if generation:
            description_parts.append(f"Generation: {generation:,.1f} {generation_units}")
        if period:
            description_parts.append(f"Year: {period}")

        description = ". ".join(description_parts) + "."

        # Determine category hierarchy
        if fuel_type:
            # Try to match fuel type to category
            fuel_upper = fuel_type.upper()
            category_hierarchy = None
            for fuel_code, categories in self.FUEL_CATEGORIES.items():
                if fuel_code in fuel_upper:
                    category_hierarchy = categories
                    break
            if not category_hierarchy:
                category_hierarchy = ["energy", "electricity", "power_plant"]
        else:
            category_hierarchy = ["energy", "electricity", "power_plant"]

        # Geographic scope
        geographic_scope = ["USA"]
        if state_id:
            geographic_scope.append(f"USA-{state_id}")

        # Quality score
        quality_score = 0.85  # EIA data is reliable
        if plant_code and state_id and consumption:
            quality_score = 0.9

        # Custom tags
        custom_tags = ["eia", "power_plant", "usa"]
        if state_id:
            custom_tags.append(state_id.lower())
        if fuel_type:
            custom_tags.append(fuel_type.lower().replace(" ", "_"))
        if sector:
            custom_tags.append(sector.lower().replace(" ", "_"))

        # Create entity
        entity = self.create_entity_dict(
            name=entity_name,
            description=description,
            entity_type="process",
            category_hierarchy=category_hierarchy,
            geographic_scope=geographic_scope,
            quality_score=quality_score,
            custom_tags=custom_tags,
            # Metadata
            plant_code=str(plant_code) if plant_code else None,
            plant_name=plant_name,
            state=state_id,
            county=county,
            sector=sector,
            fuel_type=fuel_type,
            consumption=consumption,
            consumption_units=consumption_units,
            generation=generation,
            generation_units=generation_units,
            period=period,
            data_source="EIA Facility Data",
            raw_data=record,
        )

        return entity

    def _parse_emissions_aggregate_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Parse CO2 emissions aggregate record."""
        # Extract fields
        state_id = (record.get("stateId") or record.get("stateid") or "").upper()
        sector_id = (record.get("sectorId") or record.get("sectorid") or "").upper()
        fuel_id = (record.get("fuelId") or record.get("fuelid") or "").upper()

        value = record.get("value") or record.get("emissions")
        units = record.get("units") or record.get("unit") or "million metric tons CO2"
        period = record.get("period") or ""

        # Skip if no value
        if value is None:
            return None

        try:
            emissions_value = float(value)
        except (ValueError, TypeError):
            return None

        # Build name components
        state_name = self.STATE_NAMES.get(state_id, state_id or "Unknown")
        sector_name = self._get_sector_name(sector_id)
        fuel_name = self._get_fuel_name(fuel_id)

        entity_name = f"{state_name} - {sector_name} CO2 Emissions from {fuel_name} ({period})"

        # Description
        description = (
            f"CO2 emissions for {state_name} in the {sector_name} sector from {fuel_name}: "
            f"{emissions_value:,.2f} {units} for year {period}. "
            f"Source: EIA State Energy Data System."
        )

        # Category hierarchy
        category_hierarchy = self.SECTOR_CATEGORIES.get(
            sector_id,
            ["energy", "emissions", "co2"]
        )

        # Geographic scope
        geographic_scope = ["USA"]
        if state_id and state_id != "US":
            geographic_scope.append(f"USA-{state_id}")

        # Quality score
        quality_score = 0.9  # EIA aggregates are high quality

        # Custom tags
        custom_tags = ["eia", "co2_emissions", "state_data", "usa"]
        if state_id:
            custom_tags.append(state_id.lower())
        if sector_id:
            custom_tags.append(sector_id.lower())
        if fuel_id:
            custom_tags.append(fuel_id.lower())

        # Create entity
        entity = self.create_entity_dict(
            name=entity_name,
            description=description,
            entity_type="process",
            category_hierarchy=category_hierarchy,
            geographic_scope=geographic_scope,
            quality_score=quality_score,
            custom_tags=custom_tags,
            # Metadata
            state_id=state_id,
            state_name=state_name,
            sector_id=sector_id,
            sector_name=sector_name,
            fuel_id=fuel_id,
            fuel_name=fuel_name,
            emissions_value=emissions_value,
            units=units,
            period=period,
            data_source="EIA CO2 Emissions Aggregates",
            raw_data=record,
        )

        return entity

    def _parse_generation_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Parse electricity generation record."""
        # Similar pattern to facility record but focused on generation
        generation = record.get("generation") or record.get("netGeneration")
        generation_units = record.get("generationUnits") or "MWh"
        state_id = (record.get("stateId") or record.get("stateid") or "").upper()
        fuel_type = record.get("fuelType") or ""
        period = record.get("period") or ""

        if generation is None:
            return None

        try:
            generation_value = float(generation)
        except (ValueError, TypeError):
            return None

        state_name = self.STATE_NAMES.get(state_id, state_id or "Unknown")
        entity_name = f"{state_name} - {fuel_type or 'Total'} Generation ({period})"

        description = (
            f"Electricity generation in {state_name} from {fuel_type or 'all sources'}: "
            f"{generation_value:,.1f} {generation_units} for period {period}."
        )

        # Category based on fuel type
        category_hierarchy = ["energy", "electricity", "generation"]

        geographic_scope = ["USA"]
        if state_id:
            geographic_scope.append(f"USA-{state_id}")

        quality_score = 0.85

        custom_tags = ["eia", "electricity_generation", "usa"]
        if state_id:
            custom_tags.append(state_id.lower())
        if fuel_type:
            custom_tags.append(fuel_type.lower().replace(" ", "_"))

        entity = self.create_entity_dict(
            name=entity_name,
            description=description,
            entity_type="energy",
            category_hierarchy=category_hierarchy,
            geographic_scope=geographic_scope,
            quality_score=quality_score,
            custom_tags=custom_tags,
            # Metadata
            state_id=state_id,
            fuel_type=fuel_type,
            generation=generation_value,
            generation_units=generation_units,
            period=period,
            data_source="EIA Electricity Generation",
            raw_data=record,
        )

        return entity

    def _parse_generic_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Parse unknown/generic EIA record format."""
        # Try to extract basic information
        name = record.get("name") or record.get("description") or "EIA Energy Data"
        value = record.get("value") or record.get("data")
        units = record.get("units") or record.get("unit") or ""
        period = record.get("period") or record.get("year") or ""

        if not value:
            return None

        entity_name = f"{name} ({period})" if period else name
        description = f"EIA energy data: {name}"
        if value and units:
            description += f" = {value} {units}"
        if period:
            description += f" for period {period}"

        entity = self.create_entity_dict(
            name=entity_name,
            description=description,
            entity_type="process",
            category_hierarchy=["energy", "data", "other"],
            geographic_scope=["USA"],
            quality_score=0.7,
            custom_tags=["eia", "generic"],
            # Metadata
            value=value,
            units=units,
            period=period,
            data_source="EIA",
            raw_data=record,
        )

        return entity

    def _get_sector_name(self, sector_id: str) -> str:
        """Get human-readable sector name."""
        sector_names = {
            "ELE": "Electric Power",
            "RES": "Residential",
            "COM": "Commercial",
            "IND": "Industrial",
            "TRA": "Transportation",
            "TT": "Total All Sectors",
        }
        return sector_names.get(sector_id, sector_id or "Unknown")

    def _get_fuel_name(self, fuel_id: str) -> str:
        """Get human-readable fuel name."""
        fuel_names = {
            "COW": "Coal",
            "NG": "Natural Gas",
            "PET": "Petroleum",
            "NUC": "Nuclear",
            "HYC": "Hydroelectric",
            "WND": "Wind",
            "SUN": "Solar",
            "GEO": "Geothermal",
            "BIO": "Biomass",
            "OTH": "Other",
            "TT": "Total All Fuels",
        }
        return fuel_names.get(fuel_id, fuel_id or "All Fuels")
