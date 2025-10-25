"""Parser agents for different data formats and sources."""

from mothra.agents.parser.base_parser import BaseParser
from mothra.agents.parser.json_parser import JSONParser
from mothra.agents.parser.xml_parser import XMLParser
from mothra.agents.parser.csv_parser import CSVParser

# Source-specific parsers
from mothra.agents.parser.uk_carbon_intensity_parser import UKCarbonIntensityParser
from mothra.agents.parser.epa_ghgrp_parser import EPAGHGRPParser
from mothra.agents.parser.eu_ets_parser import EUETSParser
from mothra.agents.parser.ipcc_emission_factors_parser import IPCCEmissionFactorParser
from mothra.agents.parser.uk_defra_parser import UKDEFRAParser
from mothra.agents.parser.epd_international_parser import EPDInternationalParser

__all__ = [
    "BaseParser",
    "JSONParser",
    "XMLParser",
    "CSVParser",
    "UKCarbonIntensityParser",
    "EPAGHGRPParser",
    "EUETSParser",
    "IPCCEmissionFactorParser",
    "UKDEFRAParser",
    "EPDInternationalParser",
]
