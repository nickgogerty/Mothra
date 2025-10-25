"""
IPCC Emission Factor Database Parser.

Parses emission factors from the IPCC EFDB (Emission Factor Database).
Website: https://www.ipcc-nggip.iges.or.jp/EFDB

The IPCC EFDB provides emission factors from the IPCC Guidelines for
National Greenhouse Gas Inventories. Data is typically scraped from HTML tables.

Example table structure:
| Source/Sink Category | Fuel/Material | Factor | Unit | Uncertainty | Reference |
|---------------------|---------------|--------|------|-------------|-----------|
| Energy - Combustion | Natural Gas   | 56.1   | kg CO2/GJ | ±5% | IPCC 2006 |
"""

from typing import Any

from mothra.agents.parser.base_parser import BaseParser
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class IPCCEmissionFactorParser(BaseParser):
    """Parser for IPCC Emission Factor Database."""

    # IPCC sector to category mapping
    SECTOR_CATEGORIES = {
        "Energy - Combustion": ["energy", "combustion", "stationary"],
        "Energy - Mobile Combustion": ["energy", "transport", "mobile"],
        "Energy - Fugitive": ["energy", "fugitive", "leakage"],
        "Industrial Processes - Mineral": ["industrial", "minerals", "non_metal"],
        "Industrial Processes - Chemical": ["industrial", "chemicals", "manufacturing"],
        "Industrial Processes - Metal": ["industrial", "metals", "manufacturing"],
        "Agriculture - Enteric Fermentation": ["agriculture", "livestock", "methane"],
        "Agriculture - Manure Management": ["agriculture", "livestock", "manure"],
        "Agriculture - Rice Cultivation": ["agriculture", "crops", "rice"],
        "Agriculture - Soil": ["agriculture", "soil", "n2o"],
        "Waste - Solid Waste Disposal": ["waste", "landfill", "disposal"],
        "Waste - Wastewater": ["waste", "wastewater", "treatment"],
        "Waste - Incineration": ["waste", "incineration", "combustion"],
        "LULUCF - Forest": ["lulucf", "forestry", "land_use"],
        "LULUCF - Cropland": ["lulucf", "cropland", "agriculture"],
        "LULUCF - Grassland": ["lulucf", "grassland", "pasture"],
    }

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse IPCC emission factor data.

        Args:
            data: Raw HTML or structured data

        Returns:
            List of entity dictionaries for emission factors
        """
        if isinstance(data, dict) or isinstance(data, list):
            return await self._parse_structured(data)
        else:
            return await self._parse_html(data)

    async def _parse_structured(self, data: dict | list) -> list[dict[str, Any]]:
        """Parse structured JSON/dict format."""
        entities = []

        # Handle both list and dict
        if isinstance(data, dict):
            records = data.get("emission_factors", []) or data.get("data", [])
        else:
            records = data

        for record in records:
            entity = self._create_emission_factor_entity(record)
            if entity:
                entities.append(entity)

        logger.info(
            "ipcc_ef_parsed",
            total_entities=len(entities),
            source=self.source.name,
        )

        return entities

    async def _parse_html(self, html: str | bytes) -> list[dict[str, Any]]:
        """Parse HTML table format."""
        from bs4 import BeautifulSoup

        if isinstance(html, bytes):
            html = html.decode("utf-8")

        soup = BeautifulSoup(html, "html.parser")
        entities = []

        # Find all tables
        tables = soup.find_all("table")

        for table in tables:
            # Try to extract emission factors from table rows
            rows = table.find_all("tr")

            # Skip header row
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) < 3:
                    continue

                # Extract data from cells (flexible column mapping)
                record = self._extract_from_cells(cells)
                if record:
                    entity = self._create_emission_factor_entity(record)
                    if entity:
                        entities.append(entity)

        logger.info(
            "ipcc_ef_html_parsed",
            total_entities=len(entities),
            tables=len(tables),
        )

        return entities

    def _extract_from_cells(self, cells: list) -> dict[str, Any] | None:
        """Extract emission factor record from table cells."""
        if len(cells) < 3:
            return None

        # Try to intelligently extract fields
        # Common patterns: [Category, Fuel, Factor, Unit, ...]
        try:
            record = {
                "sector": cells[0].get_text(strip=True),
                "fuel_material": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                "factor": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                "unit": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                "uncertainty": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                "reference": cells[5].get_text(strip=True) if len(cells) > 5 else "IPCC",
            }
            return record
        except Exception as e:
            logger.debug("cell_extraction_failed", error=str(e))
            return None

    def _create_emission_factor_entity(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Create entity from emission factor record."""
        # Extract fields
        sector = record.get("sector") or record.get("category") or ""
        fuel_material = (record.get("fuel_material") or record.get("fuel") or
                        record.get("material") or record.get("activity") or "")
        factor = record.get("factor") or record.get("emission_factor") or record.get("value")
        unit = record.get("unit") or ""
        uncertainty = record.get("uncertainty") or ""
        reference = record.get("reference") or "IPCC"

        # Skip if no factor value
        if not factor:
            return None

        try:
            factor_value = float(str(factor).replace(",", "").replace(" ", "").strip())
        except (ValueError, TypeError):
            return None

        # Get category hierarchy
        category_hierarchy = None
        for sector_key, categories in self.SECTOR_CATEGORIES.items():
            if sector_key in sector:
                category_hierarchy = categories
                break

        if not category_hierarchy:
            category_hierarchy = ["emission_factors", "ipcc", "other"]

        # Build name
        if fuel_material:
            name = f"IPCC Emission Factor: {fuel_material} - {sector}"
        else:
            name = f"IPCC Emission Factor: {sector}"

        # Build description
        description = (
            f"IPCC emission factor for {fuel_material if fuel_material else sector}. "
            f"Factor: {factor_value} {unit}. "
        )
        if uncertainty:
            description += f"Uncertainty: {uncertainty}. "
        description += f"Reference: {reference}."

        # Quality score
        quality_score = 0.9  # IPCC data is authoritative

        # Custom tags
        custom_tags = ["ipcc", "emission_factor", "global"]
        if sector:
            custom_tags.append(sector.lower().replace(" ", "_").replace("-", "_"))
        if fuel_material:
            custom_tags.append(fuel_material.lower().replace(" ", "_"))

        # Create entity
        entity = self.create_entity_dict(
            name=name,
            description=description,
            entity_type="process",
            category_hierarchy=category_hierarchy,
            geographic_scope=["Global"],
            quality_score=quality_score,
            custom_tags=custom_tags,
            # Metadata
            sector=sector,
            fuel_material=fuel_material,
            emission_factor=factor_value,
            unit=unit,
            uncertainty=uncertainty,
            reference=reference,
            data_source="IPCC EFDB",
            raw_data=record,
        )

        return entity
