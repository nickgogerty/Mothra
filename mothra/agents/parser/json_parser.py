"""JSON parser for carbon data."""

import json
from typing import Any

from mothra.agents.parser.base_parser import BaseParser


class JSONParser(BaseParser):
    """Parser for JSON-formatted carbon data."""

    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse JSON data.

        Args:
            data: JSON string or dict

        Returns:
            List of parsed entities
        """
        try:
            if isinstance(data, str):
                parsed = json.loads(data)
            else:
                parsed = data

            # Handle different JSON structures
            if isinstance(parsed, list):
                return [self.standardize_entity(record) for record in parsed]
            elif isinstance(parsed, dict):
                # Check if there's a data array
                if "data" in parsed:
                    return [self.standardize_entity(record) for record in parsed["data"]]
                elif "results" in parsed:
                    return [self.standardize_entity(record) for record in parsed["results"]]
                else:
                    # Single record
                    return [self.standardize_entity(parsed)]

            return []

        except json.JSONDecodeError as e:
            self.logger.error("json_parse_error", error=str(e))
            return []
        except Exception as e:
            self.logger.error("unexpected_parse_error", error=str(e))
            return []
