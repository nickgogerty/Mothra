"""XML parser for carbon data."""

from typing import Any

import xmltodict

from mothra.agents.parser.base_parser import BaseParser


class XMLParser(BaseParser):
    """Parser for XML-formatted carbon data."""

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse XML data.

        Args:
            data: XML string

        Returns:
            List of parsed entities
        """
        try:
            if not isinstance(data, str):
                data = str(data)

            parsed = xmltodict.parse(data)

            # Extract entities from common XML structures
            entities = []

            # Try to find data array in various locations
            if "root" in parsed:
                root = parsed["root"]
                if "data" in root:
                    data_items = root["data"]
                    if isinstance(data_items, list):
                        entities = [self.standardize_entity(item) for item in data_items]
                    else:
                        entities = [self.standardize_entity(data_items)]

            return entities

        except Exception as e:
            self.logger.error("xml_parse_error", error=str(e))
            return []
