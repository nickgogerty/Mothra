"""
EIA (Energy Information Administration) Integration.

Connects to EIA's Open Data API v2 to fetch:
- State-level CO2 emissions data (1960-present)
- Power plant facility emissions (15,000+ facilities)
- Electricity generation by fuel type
- Carbon coefficients and emission factors
- Energy consumption by sector

API Base URL: https://api.eia.gov/v2/
API Docs: https://www.eia.gov/opendata/documentation.php
API Dashboard: https://www.eia.gov/opendata/browser/

AUTHENTICATION:
- Get free API key from: https://www.eia.gov/opendata/
- Set EIA_API_KEY environment variable or pass api_key parameter
- API key passed as query parameter: ?api_key=YOUR_KEY

KEY ENDPOINTS:
- /electricity/facility-fuel/data - Plant-level emissions & fuel data
- /co2-emissions/co2-emissions-aggregates/data - State CO2 emissions
- /electricity/rto/fuel-type-data/data - Grid fuel mix by region
- /seds/data - State Energy Data System (comprehensive state data)
"""

import asyncio
import os
from datetime import datetime
from typing import Any
from urllib.parse import urlencode

import aiohttp

from mothra.config import settings
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class EIAClient:
    """
    Client for EIA (Energy Information Administration) Open Data API v2.

    Simple API key authentication via query parameters.
    """

    BASE_URL = "https://api.eia.gov/v2"

    # Retry configuration
    MAX_RETRIES = 4
    RETRY_DELAYS = [2, 4, 8, 16]  # Exponential backoff in seconds

    # Rate limiting - EIA doesn't publish specific limits, but being conservative
    DEFAULT_RATE_LIMIT = 100  # requests per minute

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        auto_load_credentials: bool = True,
    ):
        """
        Initialize EIA Client.

        Args:
            api_key: EIA API key
            base_url: Override default base URL
            auto_load_credentials: Automatically load API key from environment (default: True)
        """
        self.base_url = base_url or os.getenv("EIA_API_BASE_URL") or self.BASE_URL
        self.session = None

        # Auto-load credentials from environment if requested
        if auto_load_credentials and not api_key:
            api_key = self._load_api_key_from_env()

        self.api_key = api_key

        if not self.api_key:
            logger.warning(
                "eia_no_authentication",
                message="No API key provided - requests may fail or be rate limited",
                recommendation="Set EIA_API_KEY environment variable",
                get_key_url="https://www.eia.gov/opendata/",
            )

    def _load_api_key_from_env(self) -> str | None:
        """Load API key from environment variables."""
        # Try to get from settings first, then fall back to os.getenv
        if hasattr(settings, 'eia_api_key'):
            return settings.eia_api_key
        return os.getenv("EIA_API_KEY")

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _request_with_retry(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        method: str = "GET",
    ) -> dict[str, Any] | None:
        """
        Make HTTP request with exponential backoff retry logic.

        Args:
            url: Full URL to request
            params: Query parameters
            method: HTTP method (default: GET)

        Returns:
            Response JSON data or None on failure
        """
        params = params or {}

        # Add API key to all requests
        if self.api_key:
            params["api_key"] = self.api_key

        for attempt in range(self.MAX_RETRIES):
            try:
                async with self.session.request(method, url, params=params) as response:
                    # Handle rate limiting
                    if response.status == 429:
                        delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                        logger.warning(
                            "eia_rate_limited",
                            attempt=attempt + 1,
                            delay_seconds=delay,
                            url=url,
                        )
                        await asyncio.sleep(delay)
                        continue

                    # Handle other errors
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            "eia_request_error",
                            status=response.status,
                            url=url,
                            error=error_text,
                            attempt=attempt + 1,
                        )

                        # Retry on 5xx errors
                        if 500 <= response.status < 600:
                            delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                            await asyncio.sleep(delay)
                            continue

                        # Don't retry on 4xx errors (except 429)
                        return None

                    # Success
                    data = await response.json()
                    logger.debug(
                        "eia_request_success",
                        url=url,
                        status=response.status,
                    )
                    return data

            except aiohttp.ClientError as e:
                delay = self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)]
                logger.warning(
                    "eia_request_exception",
                    exception=str(e),
                    attempt=attempt + 1,
                    delay_seconds=delay,
                    url=url,
                )
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(
                    "eia_unexpected_error",
                    exception=str(e),
                    exception_type=type(e).__name__,
                    url=url,
                )
                return None

        # All retries exhausted
        logger.error(
            "eia_max_retries_exceeded",
            max_retries=self.MAX_RETRIES,
            url=url,
        )
        return None

    async def get_endpoint(
        self,
        route: str,
        data: bool = True,
        facets: dict[str, list[str]] | None = None,
        frequency: str | None = None,
        data_columns: list[str] | None = None,
        sort: list[dict[str, str]] | None = None,
        offset: int = 0,
        length: int = 5000,
        **kwargs,
    ) -> dict[str, Any] | None:
        """
        Get data from any EIA API endpoint.

        Args:
            route: API route (e.g., 'electricity/facility-fuel', 'co2-emissions/co2-emissions-aggregates')
            data: If True, append '/data' to route (default: True)
            facets: Filter dimensions (e.g., {'stateId': ['CA', 'NY'], 'sectorId': ['RES']})
            frequency: Data frequency (e.g., 'annual', 'monthly', 'quarterly')
            data_columns: Specific data columns to return (e.g., ['value', 'units'])
            sort: Sort specification (e.g., [{'column': 'period', 'direction': 'desc'}])
            offset: Pagination offset (default: 0)
            length: Number of records to return (default: 5000, max: 5000)
            **kwargs: Additional query parameters

        Returns:
            API response data or None on failure

        Example:
            # Get California facility data
            data = await client.get_endpoint(
                route='electricity/facility-fuel',
                facets={'stateid': ['CA']},
                frequency='monthly',
                length=1000
            )
        """
        # Build URL
        if data:
            url = f"{self.base_url}/{route.strip('/')}/data"
        else:
            url = f"{self.base_url}/{route.strip('/')}"

        # Build query parameters
        params = {
            "offset": offset,
            "length": min(length, 5000),  # EIA max is 5000
            **kwargs,
        }

        # Add frequency if provided
        if frequency:
            params["frequency"] = frequency

        # Add data columns if provided
        if data_columns:
            for col in data_columns:
                params[f"data[{col}]"] = col

        # Add facets (filters)
        if facets:
            for facet_name, values in facets.items():
                for value in values:
                    # Create unique parameter key for each facet value
                    # EIA uses: facets[stateId][]=CA&facets[stateId][]=NY
                    key = f"facets[{facet_name}][]"
                    if key not in params:
                        params[key] = []
                    if isinstance(params[key], list):
                        params[key].append(value)
                    else:
                        params[key] = [params[key], value]

        # Add sort if provided
        if sort:
            for i, sort_spec in enumerate(sort):
                params[f"sort[{i}][column]"] = sort_spec.get("column")
                params[f"sort[{i}][direction]"] = sort_spec.get("direction", "asc")

        return await self._request_with_retry(url, params)

    async def get_all_pages(
        self,
        route: str,
        max_records: int | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """
        Fetch all pages of data from an endpoint.

        Args:
            route: API route
            max_records: Maximum number of records to fetch (None = all)
            **kwargs: Additional parameters passed to get_endpoint()

        Returns:
            List of all records
        """
        all_records = []
        offset = 0
        length = 5000  # Maximum per request

        while True:
            response = await self.get_endpoint(
                route=route,
                offset=offset,
                length=length,
                **kwargs,
            )

            if not response:
                logger.warning(
                    "eia_pagination_failed",
                    route=route,
                    offset=offset,
                )
                break

            # Extract records from response
            records = response.get("response", {}).get("data", [])

            if not records:
                logger.info(
                    "eia_pagination_complete",
                    route=route,
                    total_records=len(all_records),
                )
                break

            all_records.extend(records)
            logger.info(
                "eia_page_fetched",
                route=route,
                offset=offset,
                records_in_page=len(records),
                total_so_far=len(all_records),
            )

            # Check if we've reached max_records
            if max_records and len(all_records) >= max_records:
                all_records = all_records[:max_records]
                logger.info(
                    "eia_max_records_reached",
                    route=route,
                    max_records=max_records,
                )
                break

            # Check if we've fetched all available records
            total_available = response.get("response", {}).get("total", 0)
            try:
                total_available = int(total_available)
            except (ValueError, TypeError):
                total_available = 0
            if len(all_records) >= total_available:
                logger.info(
                    "eia_all_records_fetched",
                    route=route,
                    total_records=len(all_records),
                )
                break

            # Move to next page
            offset += length

        return all_records

    async def get_facility_fuel_data(
        self,
        state_ids: list[str] | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        frequency: str = "annual",
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get electricity facility fuel consumption and emissions data.

        This is the primary endpoint for power plant emissions data.

        Args:
            state_ids: List of state codes (e.g., ['CA', 'NY']) or None for all states
            start_date: Start date (YYYY or YYYY-MM format depending on frequency)
            end_date: End date (YYYY or YYYY-MM format)
            frequency: 'annual' or 'monthly' (default: 'annual')
            max_records: Maximum records to fetch (None = all)

        Returns:
            List of facility records with emissions data
        """
        kwargs = {"frequency": frequency}
        facets = {}

        if state_ids:
            facets["state"] = state_ids

        if start_date:
            kwargs["start"] = start_date
        if end_date:
            kwargs["end"] = end_date

        return await self.get_all_pages(
            route="electricity/facility-fuel",
            facets=facets if facets else None,
            max_records=max_records,
            **kwargs,
        )

    async def get_co2_emissions_aggregates(
        self,
        state_ids: list[str] | None = None,
        sectors: list[str] | None = None,
        fuel_types: list[str] | None = None,
        start_year: str | None = None,
        end_year: str | None = None,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get state-level CO2 emissions aggregates.

        Args:
            state_ids: List of state codes or None for all
            sectors: List of sector codes (e.g., ['RES', 'COM', 'IND', 'TRA', 'ELE'])
            fuel_types: List of fuel type codes
            start_year: Start year (YYYY)
            end_year: End year (YYYY)
            max_records: Maximum records to fetch

        Returns:
            List of CO2 emissions records
        """
        kwargs = {"frequency": "annual"}
        facets = {}

        if state_ids:
            facets["stateId"] = state_ids
        if sectors:
            facets["sectorId"] = sectors
        if fuel_types:
            facets["fuelId"] = fuel_types

        if start_year:
            kwargs["start"] = start_year
        if end_year:
            kwargs["end"] = end_year

        return await self.get_all_pages(
            route="co2-emissions/co2-emissions-aggregates",
            facets=facets if facets else None,
            max_records=max_records,
            **kwargs,
        )

    async def get_seds_co2_emissions(
        self,
        state_ids: list[str] | None = None,
        start_year: str | None = None,
        end_year: str | None = None,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get CO2 emissions data from SEDS (State Energy Data System).

        This uses the SEDS API which has actual CO2 emission values.
        Fetches series that contain CO2 emissions by fuel and sector.

        Args:
            state_ids: List of state codes or None for all
            start_year: Start year (YYYY)
            end_year: End year (YYYY)
            max_records: Maximum records to fetch

        Returns:
            List of CO2 emissions records with values (filtered for CO2 series only)
        """
        kwargs = {"frequency": "annual", "data_columns": ["value"]}
        facets = {}

        if state_ids:
            facets["stateId"] = state_ids

        # Filter for CO2 emission series - all series ending in "CE" are CO2 emissions
        # Format: [fuel][sector]CE where CE = CO2 emissions
        # Examples: CLTCE (coal total), NGTCE (natural gas total), CLEIE (coal electric power)
        # We'll fetch a large set and filter client-side since API doesn't support wildcards
        co2_series = [
            # Coal emissions by sector
            "CLTCE", "CLEIE", "CLICE", "CLCCE", "CLRCE", "CLACE",
            # Natural gas emissions by sector
            "NGTCE", "NGEIE", "NGICE", "NGCCE", "NGRCE", "NGACE",
            # Petroleum emissions by sector
            "PATCE", "PAEIE", "PAICE", "PACCE", "PARACE", "PAACE",
            # Fossil fuel totals by sector
            "FFTCE", "FFEIE", "FFICE", "FFCCE", "FFRCE", "FFACE",
            # Carbon intensity metrics
            "CDTPR", "CDEGR", "CDTCR",
        ]
        facets["seriesId"] = co2_series

        if start_year:
            kwargs["start"] = start_year
        if end_year:
            kwargs["end"] = end_year

        return await self.get_all_pages(
            route="seds",
            facets=facets if facets else None,
            max_records=max_records,
            **kwargs,
        )

    async def get_electricity_generation(
        self,
        state_ids: list[str] | None = None,
        frequency: str = "annual",
        start_date: str | None = None,
        end_date: str | None = None,
        max_records: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get electricity generation data by state and fuel type.

        Args:
            state_ids: List of state codes
            frequency: 'annual' or 'monthly'
            start_date: Start date
            end_date: End date
            max_records: Maximum records to fetch

        Returns:
            List of generation records
        """
        kwargs = {"frequency": frequency}
        facets = {}

        if state_ids:
            facets["stateId"] = state_ids

        if start_date:
            kwargs["start"] = start_date
        if end_date:
            kwargs["end"] = end_date

        return await self.get_all_pages(
            route="electricity/electric-power-operational-data",
            facets=facets if facets else None,
            max_records=max_records,
            **kwargs,
        )

    async def extract_all_high_volume_data(
        self,
        max_records_per_endpoint: int = 20000,
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Extract data from high-volume endpoints to quickly reach 15K+ records.

        This targets the endpoints most likely to have large amounts of data:
        1. Facility fuel data (15,000+ power plants)
        2. CO2 emissions aggregates (state x year x sector x fuel)

        Args:
            max_records_per_endpoint: Max records per endpoint

        Returns:
            Dict mapping endpoint names to record lists
        """
        logger.info(
            "eia_extraction_start",
            target_records=max_records_per_endpoint * 2,
        )

        results = {}

        # 1. Facility fuel data - most records available
        logger.info("Fetching facility fuel data...")
        results["facility_fuel"] = await self.get_facility_fuel_data(
            frequency="annual",
            max_records=max_records_per_endpoint,
        )

        # 2. CO2 emissions aggregates
        logger.info("Fetching CO2 emissions aggregates...")
        results["co2_emissions"] = await self.get_co2_emissions_aggregates(
            max_records=max_records_per_endpoint,
        )

        total_records = sum(len(records) for records in results.values())
        logger.info(
            "eia_extraction_complete",
            total_records=total_records,
            breakdown={k: len(v) for k, v in results.items()},
        )

        return results


async def test_eia_client():
    """Test EIA client functionality."""
    async with EIAClient() as client:
        # Test facility fuel data
        print("\nTesting facility fuel data...")
        facilities = await client.get_facility_fuel_data(
            state_ids=["CA"],
            frequency="annual",
            max_records=10,
        )
        print(f"Fetched {len(facilities)} facility records")
        if facilities:
            print(f"Sample record keys: {facilities[0].keys()}")

        # Test CO2 emissions
        print("\nTesting CO2 emissions aggregates...")
        emissions = await client.get_co2_emissions_aggregates(
            state_ids=["CA"],
            max_records=10,
        )
        print(f"Fetched {len(emissions)} emissions records")
        if emissions:
            print(f"Sample record keys: {emissions[0].keys()}")


if __name__ == "__main__":
    asyncio.run(test_eia_client())
