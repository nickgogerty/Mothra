"""
Parser Registry: Maps data sources to their appropriate parsers.

The registry automatically selects the correct parser based on the data source name
or can fall back to generic parsers based on data format.
"""

from typing import Type

from mothra.agents.parser.base_parser import BaseParser
from mothra.agents.parser.uk_carbon_intensity_parser import UKCarbonIntensityParser
from mothra.agents.parser.epa_ghgrp_parser import EPAGHGRPParser
from mothra.agents.parser.eia_parser import EIAParser
from mothra.agents.parser.eu_ets_parser import EUETSParser
from mothra.agents.parser.ipcc_emission_factors_parser import IPCCEmissionFactorParser
from mothra.agents.parser.uk_defra_parser import UKDEFRAParser
from mothra.agents.parser.epd_international_parser import EPDInternationalParser
from mothra.db.models import DataSource
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class ParserRegistry:
    """Registry for mapping data sources to parsers."""

    # Map source names to parser classes
    _PARSERS: dict[str, Type[BaseParser]] = {
        # UK Sources
        "UK Carbon Intensity API": UKCarbonIntensityParser,
        "UK DEFRA Conversion Factors": UKDEFRAParser,

        # USA Sources
        "EPA GHGRP": EPAGHGRPParser,
        "EPA Greenhouse Gas Reporting Program": EPAGHGRPParser,
        "EIA": EIAParser,
        "EIA Energy Data": EIAParser,
        "Energy Information Administration": EIAParser,

        # EU Sources
        "EU ETS": EUETSParser,
        "EU Emissions Trading System": EUETSParser,

        # Global Sources
        "IPCC EFDB": IPCCEmissionFactorParser,
        "IPCC Emission Factor Database": IPCCEmissionFactorParser,

        # EPD Sources
        "International EPD System": EPDInternationalParser,
        "IBU EPD Database": EPDInternationalParser,
        "EPD Norge": EPDInternationalParser,
        "Australasian EPD Programme": EPDInternationalParser,
        "FDES INIES": EPDInternationalParser,
    }

    @classmethod
    def get_parser(cls, source: DataSource) -> BaseParser | None:
        """
        Get the appropriate parser for a data source.

        Args:
            source: DataSource to get parser for

        Returns:
            Parser instance, or None if no parser found
        """
        # Try exact name match first
        parser_class = cls._PARSERS.get(source.name)

        if parser_class:
            logger.info(
                "parser_found",
                source=source.name,
                parser=parser_class.__name__,
            )
            return parser_class(source)

        # Try partial name matching
        for source_pattern, parser_class in cls._PARSERS.items():
            if source_pattern.lower() in source.name.lower():
                logger.info(
                    "parser_found_partial",
                    source=source.name,
                    pattern=source_pattern,
                    parser=parser_class.__name__,
                )
                return parser_class(source)

        # No parser found
        logger.warning(
            "no_parser_found",
            source=source.name,
            available_parsers=list(cls._PARSERS.keys()),
        )
        return None

    @classmethod
    def register_parser(
        cls, source_name: str, parser_class: Type[BaseParser]
    ) -> None:
        """
        Register a new parser for a data source.

        Args:
            source_name: Name or pattern to match against source names
            parser_class: Parser class to use for this source
        """
        cls._PARSERS[source_name] = parser_class
        logger.info(
            "parser_registered",
            source_name=source_name,
            parser=parser_class.__name__,
        )

    @classmethod
    def list_parsers(cls) -> dict[str, str]:
        """
        List all registered parsers.

        Returns:
            Dict mapping source names to parser class names
        """
        return {
            source: parser.__name__
            for source, parser in cls._PARSERS.items()
        }

    @classmethod
    def has_parser(cls, source: DataSource) -> bool:
        """
        Check if a parser exists for a source.

        Args:
            source: DataSource to check

        Returns:
            True if parser exists, False otherwise
        """
        return cls.get_parser(source) is not None
