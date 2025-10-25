"""
Base parser interface for data extraction.

Parsers extract structured carbon data from raw responses and convert them
into CarbonEntity-compatible dictionaries.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any

from mothra.db.models import DataSource
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class BaseParser(ABC):
    """Base class for all data source parsers."""

    def __init__(self, source: DataSource) -> None:
        """
        Initialize parser with data source.

        Args:
            source: DataSource this parser handles
        """
        self.source = source
        self.parser_name = self.__class__.__name__
        self.logger = logger
        logger.info(
            "parser_initialized",
            parser=self.parser_name,
            source=source.name,
        )

    @abstractmethod
    async def parse(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse raw data into standardized entity dictionaries.

        Args:
            data: Raw data to parse

        Returns:
            List of parsed entity dictionaries ready for CarbonEntity creation
        """
        pass

    def create_entity_dict(
        self,
        name: str,
        description: str,
        entity_type: str,
        category_hierarchy: list[str],
        geographic_scope: list[str],
        quality_score: float = 0.5,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Create standardized entity dictionary.

        Args:
            name: Entity name
            description: Entity description
            entity_type: process, material, product, service, energy
            category_hierarchy: List of categories from general to specific
            geographic_scope: List of geographic regions
            quality_score: Data quality score (0-1)
            **kwargs: Additional fields for extra_metadata

        Returns:
            Dictionary with all required CarbonEntity fields
        """
        entity_dict = {
            "id": uuid.uuid4(),
            "source_id": self.source.name,
            "source_uuid": self.source.id,
            "name": name,
            "description": description,
            "entity_type": entity_type,
            "category_hierarchy": category_hierarchy,
            "geographic_scope": geographic_scope,
            "quality_score": quality_score,
            "custom_tags": kwargs.pop("custom_tags", []),
            "raw_data": kwargs.pop("raw_data", {}),
            "extra_metadata": kwargs,  # All remaining kwargs go to metadata
        }

        return entity_dict

    def validate_entity(self, entity_dict: dict[str, Any]) -> bool:
        """
        Validate entity dictionary before database insertion.

        Args:
            entity_dict: Entity dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "name",
            "entity_type",
            "source_id",
        ]

        for field in required_fields:
            if field not in entity_dict or not entity_dict[field]:
                logger.warning(
                    "entity_validation_failed",
                    field=field,
                    entity_name=entity_dict.get("name", "unknown"),
                )
                return False

        # Validate entity_type
        valid_types = ["process", "material", "product", "service", "energy"]
        if entity_dict["entity_type"] not in valid_types:
            logger.warning(
                "invalid_entity_type",
                entity_type=entity_dict["entity_type"],
                valid_types=valid_types,
            )
            return False

        return True

    async def parse_and_validate(self, data: Any) -> list[dict[str, Any]]:
        """
        Parse raw data and validate results.

        Args:
            data: Raw response data from crawler

        Returns:
            List of validated entity dictionaries
        """
        try:
            entities = await self.parse(data)

            # Validate all entities
            valid_entities = [e for e in entities if self.validate_entity(e)]

            logger.info(
                "parse_complete",
                parser=self.parser_name,
                total=len(entities),
                valid=len(valid_entities),
                invalid=len(entities) - len(valid_entities),
            )

            return valid_entities

        except Exception as e:
            logger.error(
                "parse_failed",
                parser=self.parser_name,
                error=str(e),
            )
            return []

    def extract_emissions_data(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """
        Extract emissions data from a record.

        Args:
            record: Data record

        Returns:
            Standardized emissions dictionary or None
        """
        # Common field mappings
        value_fields = ["value", "emission_factor", "co2e", "ghg_emissions", "carbon_value", "intensity"]
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
