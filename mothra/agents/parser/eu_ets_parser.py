"""
EU ETS (Emissions Trading System) Parser.

Parses verified emissions data from the EU Emissions Trading System.
Data Portal: https://ec.europa.eu/clima/ets
API Format: XML or JSON depending on endpoint

Example XML structure:
<installations>
  <installation>
    <accountID>12345</accountID>
    <installationName>Example Power Plant</installationName>
    <permitID>DE-123-456</permitID>
    <country>Germany</country>
    <mainActivityType>Combustion of fuels</mainActivityType>
    <year>2022</year>
    <verifiedEmissions>1500000</verifiedEmissions>
    <unit>tCO2e</unit>
  </installation>
</installations>
"""

import json
import xml.etree.ElementTree as ET
from typing import Any

from mothra.agents.parser.base_parser import BaseParser
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class EUETSParser(BaseParser):
    """Parser for EU ETS verified emissions data."""

    # Activity type to category mapping
    ACTIVITY_CATEGORIES = {
        "Combustion of fuels": ["energy", "combustion", "power_generation"],
        "Refining of mineral oil": ["industrial", "refining", "petroleum"],
        "Production of coke": ["industrial", "steel", "coke"],
        "Metal ore roasting or sintering": ["industrial", "metals", "processing"],
        "Production of pig iron or steel": ["industrial", "steel", "primary_production"],
        "Production of cement clinker": ["industrial", "cement", "construction_materials"],
        "Production of lime": ["industrial", "lime", "construction_materials"],
        "Production of glass": ["industrial", "glass", "manufacturing"],
        "Production of ceramics": ["industrial", "ceramics", "manufacturing"],
        "Production of pulp": ["industrial", "pulp_paper", "manufacturing"],
        "Production of paper": ["industrial", "pulp_paper", "manufacturing"],
        "Production of carbon black": ["industrial", "chemicals", "manufacturing"],
        "Production of nitric acid": ["industrial", "chemicals", "acids"],
        "Production of adipic acid": ["industrial", "chemicals", "acids"],
        "Production of glyoxal": ["industrial", "chemicals", "manufacturing"],
        "Production of ammonia": ["industrial", "chemicals", "fertilizer"],
        "Production of aluminium": ["industrial", "metals", "aluminum"],
    }

    # EU country codes
    EU_COUNTRIES = {
        "AT": "Austria", "BE": "Belgium", "BG": "Bulgaria", "HR": "Croatia",
        "CY": "Cyprus", "CZ": "Czech Republic", "DK": "Denmark", "EE": "Estonia",
        "FI": "Finland", "FR": "France", "DE": "Germany", "GR": "Greece",
        "HU": "Hungary", "IE": "Ireland", "IT": "Italy", "LV": "Latvia",
        "LT": "Lithuania", "LU": "Luxembourg", "MT": "Malta", "NL": "Netherlands",
        "PL": "Poland", "PT": "Portugal", "RO": "Romania", "SK": "Slovakia",
        "SI": "Slovenia", "ES": "Spain", "SE": "Sweden"
    }

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse EU ETS API response (XML or JSON).

        Args:
            data: Raw API response (XML string, JSON string, bytes, or dict)

        Returns:
            List of entity dictionaries for installation emissions
        """
        # Detect format and parse accordingly
        if isinstance(data, dict):
            return await self._parse_json(data)
        elif isinstance(data, (str, bytes)):
            if isinstance(data, bytes):
                data_str = data.decode("utf-8")
            else:
                data_str = data

            # Try JSON first
            if data_str.strip().startswith(("{", "[")):
                try:
                    json_data = json.loads(data_str)
                    return await self._parse_json(json_data)
                except json.JSONDecodeError:
                    pass

            # Try XML
            try:
                return await self._parse_xml(data_str)
            except ET.ParseError:
                logger.error("failed_to_parse_eu_ets", error="Invalid XML/JSON format")
                return []
        else:
            logger.error("unsupported_data_type", data_type=type(data))
            return []

    async def _parse_xml(self, xml_str: str) -> list[dict[str, Any]]:
        """Parse XML format EU ETS data."""
        root = ET.fromstring(xml_str)
        entities = []

        # Handle different XML root elements
        installations = root.findall(".//installation") or root.findall(".//Installation")

        for installation in installations:
            entity = self._extract_installation_data(installation)
            if entity:
                entities.append(entity)

        return entities

    async def _parse_json(self, json_data: dict | list) -> list[dict[str, Any]]:
        """Parse JSON format EU ETS data."""
        entities = []

        # Handle list or dict with data key
        if isinstance(json_data, list):
            records = json_data
        else:
            records = json_data.get("installations", []) or json_data.get("data", [])

        for record in records:
            entity = self._extract_installation_dict(record)
            if entity:
                entities.append(entity)

        return entities

    def _extract_installation_data(self, element: ET.Element) -> dict[str, Any] | None:
        """Extract data from XML element."""
        # Helper to get text from element
        def get_text(tag: str) -> str:
            elem = element.find(tag) or element.find(tag.lower()) or element.find(tag.capitalize())
            return elem.text if elem is not None and elem.text else ""

        account_id = get_text("accountID") or get_text("account_id")
        name = get_text("installationName") or get_text("name")
        permit_id = get_text("permitID") or get_text("permit_id")
        country = get_text("country")
        activity = get_text("mainActivityType") or get_text("activity_type")
        year = get_text("year") or get_text("reporting_year")
        emissions = get_text("verifiedEmissions") or get_text("emissions")
        unit = get_text("unit") or "tCO2e"

        # Convert to dict and use common extraction
        record = {
            "account_id": account_id,
            "name": name,
            "permit_id": permit_id,
            "country": country,
            "activity_type": activity,
            "year": year,
            "emissions": emissions,
            "unit": unit,
        }

        return self._extract_installation_dict(record)

    def _extract_installation_dict(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Extract entity from installation dict (common logic for JSON/XML)."""
        # Extract fields with multiple possible keys
        name = (record.get("installationName") or record.get("name") or
                record.get("installation_name") or "Unknown Installation")
        account_id = (record.get("accountID") or record.get("account_id") or
                     record.get("id") or "")
        permit_id = (record.get("permitID") or record.get("permit_id") or
                    record.get("permit") or "")
        country = record.get("country") or record.get("country_code") or ""
        activity = (record.get("mainActivityType") or record.get("activity_type") or
                   record.get("activity") or "Unknown Activity")
        year = record.get("year") or record.get("reporting_year") or ""
        emissions = (record.get("verifiedEmissions") or record.get("emissions") or
                    record.get("verified_emissions"))
        unit = record.get("unit") or "tCO2e"

        # Skip if no emissions data
        if not emissions:
            return None

        try:
            emissions_value = float(emissions)
        except (ValueError, TypeError):
            return None

        # Get category hierarchy
        category_hierarchy = self.ACTIVITY_CATEGORIES.get(
            activity,
            ["industrial", "other", "eu_ets"]
        )

        # Build geographic scope
        geographic_scope = ["EU"]
        country_name = self.EU_COUNTRIES.get(country, country)
        if country_name:
            geographic_scope.append(country_name)

        # Build description
        description = (
            f"{name} in {country_name} reported {emissions_value:,.0f} {unit} "
            f"of verified CO2 equivalent emissions for year {year}. "
            f"Main activity: {activity}. Permit ID: {permit_id}."
        )

        # Quality score - EU ETS data is very high quality (verified)
        quality_score = 0.95

        # Entity name
        entity_name = f"{name} - EU ETS Verified Emissions ({year})"

        # Custom tags
        custom_tags = ["eu_ets", "verified_emissions", "eu", "carbon_trading"]
        if country:
            custom_tags.append(country.lower())
        if activity:
            custom_tags.append(activity.lower().replace(" ", "_"))

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
            account_id=account_id,
            permit_id=permit_id,
            installation_name=name,
            country=country,
            country_name=country_name,
            activity_type=activity,
            reporting_year=year,
            emissions_value=emissions_value,
            unit=unit,
            data_source="EU ETS",
            raw_data=record,
        )

        return entity
