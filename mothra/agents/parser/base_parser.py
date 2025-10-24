"""
Base parser interface for data extraction.
"""

from abc import ABC, abstractmethod
from typing import Any

from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class BaseParser(ABC):
    """Base class for all data format parsers."""

    def __init__(self) -> None:
        self.logger = logger

    @abstractmethod
    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse data into standardized format.

        Args:
            data: Raw data to parse

        Returns:
            List of parsed entity dictionaries
        """
        pass

    def extract_emissions_data(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """
        Extract emissions data from a record.

        Args:
            record: Data record

        Returns:
            Standardized emissions dictionary or None
        """
        # Common field mappings
        value_fields = ["value", "emission_factor", "co2e", "ghg_emissions", "carbon_value"]
        unit_fields = ["unit", "units", "emission_unit"]

        emissions = {}

        # Try to find emission value
        for field in value_fields:
            if field in record:
                try:
                    emissions["value"] = float(record[field])
                    break
                except (ValueError, TypeError):
                    continue

        # Try to find unit
        for field in unit_fields:
            if field in record:
                emissions["unit"] = str(record[field])
                break

        if "value" in emissions and "unit" in emissions:
            return emissions

        return None

    def standardize_entity(self, record: dict[str, Any]) -> dict[str, Any]:
        """
        Standardize a record into carbon entity format.

        Args:
            record: Raw record

        Returns:
            Standardized entity dictionary
        """
        return {
            "name": record.get("name", ""),
            "description": record.get("description", ""),
            "entity_type": record.get("type", "process"),
            "source_id": record.get("id", ""),
            "raw_data": record,
            "metadata": {
                "source": record.get("source", ""),
                "version": record.get("version", ""),
            },
        }
