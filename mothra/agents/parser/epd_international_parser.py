"""
International EPD System Parser.

Parses Environmental Product Declarations from the International EPD System.
Website: https://www.environdec.com/EPD-Search

EPDs provide lifecycle carbon footprint data for products. Data is typically
scraped from HTML pages or extracted from PDF documents.

Example EPD data structure:
{
    "product_name": "Concrete C30/37",
    "manufacturer": "Example Cement Company",
    "epd_number": "S-P-12345",
    "valid_until": "2025-12-31",
    "declared_unit": "1 m³",
    "gwp_total": "350",
    "gwp_unit": "kg CO2e",
    "gwp_a1_a3": "320",  # Production stages
    "product_category": "Construction products"
}
"""

import json
from typing import Any

from mothra.agents.parser.base_parser import BaseParser
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class EPDInternationalParser(BaseParser):
    """Parser for International EPD System declarations."""

    # Product category to category hierarchy mapping
    PRODUCT_CATEGORIES = {
        "Construction products": ["materials", "construction", "building_products"],
        "Concrete": ["materials", "construction", "concrete"],
        "Steel": ["materials", "metals", "steel"],
        "Aluminum": ["materials", "metals", "aluminum"],
        "Insulation": ["materials", "construction", "insulation"],
        "Windows": ["materials", "construction", "windows"],
        "Flooring": ["materials", "construction", "flooring"],
        "Roofing": ["materials", "construction", "roofing"],
        "Furniture": ["products", "furniture", "indoor"],
        "Electronics": ["products", "electronics", "appliances"],
        "Packaging": ["materials", "packaging", "containers"],
        "Textiles": ["materials", "textiles", "fabrics"],
        "Chemicals": ["materials", "chemicals", "industrial"],
        "Food products": ["products", "food", "agriculture"],
    }

    # Lifecycle stages
    LIFECYCLE_STAGES = {
        "A1-A3": "Product stage (raw material extraction and manufacturing)",
        "A4": "Transport to site",
        "A5": "Construction/installation",
        "B1-B7": "Use stage",
        "C1-C4": "End of life stage",
        "D": "Benefits beyond system boundary"
    }

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse EPD data.

        Args:
            data: Raw EPD data (dict, list, or string)

        Returns:
            List of entity dictionaries for EPDs
        """
        if isinstance(data, dict):
            return await self._parse_single_epd(data)
        elif isinstance(data, list):
            return await self._parse_multiple_epds(data)
        elif isinstance(data, (str, bytes)):
            # Try to parse as JSON
            try:
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                json_data = json.loads(data)
                if isinstance(json_data, list):
                    return await self._parse_multiple_epds(json_data)
                else:
                    return await self._parse_single_epd(json_data)
            except json.JSONDecodeError:
                # Could be HTML - would need BeautifulSoup + PDF extraction
                logger.warning("epd_html_parsing_not_implemented")
                return []
        else:
            return []

    async def _parse_single_epd(self, data: dict) -> list[dict[str, Any]]:
        """Parse a single EPD record."""
        entity = self._create_epd_entity(data)
        return [entity] if entity else []

    async def _parse_multiple_epds(self, data: list) -> list[dict[str, Any]]:
        """Parse multiple EPD records."""
        entities = []
        for record in data:
            entity = self._create_epd_entity(record)
            if entity:
                entities.append(entity)

        logger.info(
            "epd_international_parsed",
            total_entities=len(entities),
        )

        return entities

    def _create_epd_entity(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Create entity from EPD record."""
        # Extract fields
        product_name = (record.get("product_name") or record.get("name") or
                       record.get("Product") or "")
        manufacturer = (record.get("manufacturer") or record.get("company") or
                       record.get("Manufacturer") or "")
        epd_number = (record.get("epd_number") or record.get("registration_number") or
                     record.get("EPD Number") or "")
        valid_until = (record.get("valid_until") or record.get("validity") or
                      record.get("Valid until") or "")
        declared_unit = (record.get("declared_unit") or record.get("functional_unit") or
                        record.get("Declared Unit") or "1 unit")

        # GWP (Global Warming Potential) data
        gwp_total = (record.get("gwp_total") or record.get("gwp") or
                    record.get("GWP Total") or record.get("carbon_footprint"))
        gwp_unit = (record.get("gwp_unit") or record.get("unit") or
                   "kg CO2e")

        # Lifecycle stage breakdown
        gwp_a1_a3 = record.get("gwp_a1_a3") or record.get("GWP A1-A3")
        gwp_a4 = record.get("gwp_a4") or record.get("GWP A4")
        gwp_c = record.get("gwp_c") or record.get("GWP C1-C4")

        # Product category
        product_category = (record.get("product_category") or record.get("category") or
                           record.get("Product Category") or "Other")

        # Geography
        geography = (record.get("geography") or record.get("region") or
                    record.get("country") or "Global")

        # Skip if no product name or GWP
        if not product_name or not gwp_total:
            return None

        try:
            gwp_value = float(gwp_total)
        except (ValueError, TypeError):
            return None

        # Get category hierarchy
        category_hierarchy = self.PRODUCT_CATEGORIES.get(
            product_category,
            ["products", "epd", "other"]
        )

        # Build name
        if manufacturer:
            name = f"{product_name} by {manufacturer} (EPD)"
        else:
            name = f"{product_name} (EPD)"

        # Build description
        description = (
            f"Environmental Product Declaration for {product_name}. "
        )

        if manufacturer:
            description += f"Manufacturer: {manufacturer}. "

        description += (
            f"Global Warming Potential: {gwp_value} {gwp_unit} per {declared_unit}. "
        )

        if gwp_a1_a3:
            description += f"Production (A1-A3): {gwp_a1_a3} {gwp_unit}. "

        if epd_number:
            description += f"EPD Registration: {epd_number}. "

        if valid_until:
            description += f"Valid until: {valid_until}. "

        # Quality score based on completeness
        quality_score = 0.85  # EPDs are third-party verified
        if gwp_a1_a3 and manufacturer:
            quality_score = 0.9  # More complete data

        # Geographic scope
        geographic_scope = [geography] if geography else ["Global"]

        # Custom tags
        custom_tags = ["epd", "lca", "product", "carbon_footprint"]
        if product_category:
            custom_tags.append(product_category.lower().replace(" ", "_"))
        if manufacturer:
            # Add manufacturer name (first word only)
            mfr_tag = manufacturer.split()[0].lower()
            if len(mfr_tag) > 2:
                custom_tags.append(mfr_tag)

        # Create entity
        entity = self.create_entity_dict(
            name=name,
            description=description,
            entity_type="product",
            category_hierarchy=category_hierarchy,
            geographic_scope=geographic_scope,
            quality_score=quality_score,
            custom_tags=custom_tags,
            # Metadata
            product_name=product_name,
            manufacturer=manufacturer,
            epd_number=epd_number,
            valid_until=valid_until,
            declared_unit=declared_unit,
            gwp_total=gwp_value,
            gwp_a1_a3=gwp_a1_a3,
            gwp_a4=gwp_a4,
            gwp_c=gwp_c,
            gwp_unit=gwp_unit,
            product_category=product_category,
            geography=geography,
            data_source="International EPD System",
            raw_data=record,
        )

        return entity
