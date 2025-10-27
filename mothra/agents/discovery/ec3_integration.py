"""
EC3 (Embodied Carbon in Construction Calculator) Integration.

Connects to Building Transparency's EC3 API to fetch:
- 90,000+ digital EPDs
- Construction material carbon footprints
- Verified environmental product declarations
- LCA data with full EN 15804 compliance

API Base URL: https://buildingtransparency.org/api
API Docs: https://buildingtransparency.org/ec3/manage-apps/api-doc/api
OAuth Guide: https://buildingtransparency.org/ec3/manage-apps/api-doc/guide

AUTHENTICATION:
- Get API key from: https://buildingtransparency.org/ec3/manage-apps/keys
- Public access (no key) is rate-limited and has restricted data access
- OAuth 2.0 supported for advanced authentication (password grant, authorization code)
- Set EC3_API_KEY environment variable or pass api_key parameter

COMPREHENSIVE ENDPOINT SUPPORT:
This integration supports ALL official EC3 API endpoints:
- Core: epds, materials, plants, projects
- Users & Orgs: users, user_groups, orgs, plant_groups
- EPD Management: epd_requests, epd_imports, industry_epds, generic_estimates
- Standards: pcrs, baselines, reference_sets, categories, standards
- Projects: civil_projects, collections, buildings, bim_projects, elements
- Integrations: procore, autodesk_takeoff, tally_projects
- And more...
"""

import asyncio
import os
import time
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import aiohttp

from mothra.config import settings
from mothra.db.models import CarbonEntity, DataSource
from mothra.db.models_verification import (
    CarbonEntityVerification,
    GHGScope,
    LCAStage,
    VerificationStandard,
    VerificationStatus,
)
from mothra.db.session import get_db_context
from mothra.utils.logging import get_logger

logger = get_logger(__name__)


class EC3Client:
    """
    Client for EC3/openEPD API with OAuth 2.0 support.

    Supports multiple authentication methods:
    1. Bearer token (API key) - Simple method
    2. OAuth 2.0 Password Grant - Username/password
    3. OAuth 2.0 Authorization Code - Full OAuth flow

    Get API key from: https://buildingtransparency.org/ec3/manage-apps/keys
    """

    BASE_URL = "https://buildingtransparency.org/api"
    OAUTH_TOKEN_URL = "https://buildingtransparency.org/api/oauth2/token"

    # Retry configuration
    MAX_RETRIES = 4
    RETRY_DELAYS = [2, 4, 8, 16]  # Exponential backoff in seconds

    def __init__(
        self,
        api_key: str = None,
        oauth_config: dict[str, Any] = None,
        base_url: str = None,
        auto_load_credentials: bool = True,
    ):
        """
        Initialize EC3 Client.

        Args:
            api_key: Bearer token for simple authentication
            oauth_config: OAuth 2.0 configuration dict with:
                - grant_type: 'password' or 'authorization_code'
                - client_id: OAuth client ID
                - client_secret: OAuth client secret
                - username: (for password grant)
                - password: (for password grant)
                - scope: (optional, default 'read')
                - code: (for authorization code grant)
            base_url: Override default base URL
            auto_load_credentials: Automatically load credentials from environment (default: True)
        """
        self.base_url = base_url or os.getenv("EC3_API_BASE_URL") or self.BASE_URL
        self.session = None
        self.access_token = None
        self.token_expiry = None

        # Auto-load credentials from environment if requested
        if auto_load_credentials and not oauth_config and not api_key:
            oauth_config = self._load_oauth_from_env()
            api_key = self._load_api_key_from_env()

        self.api_key = api_key
        self.oauth_config = oauth_config

    def _load_api_key_from_env(self) -> str | None:
        """Load API key from environment variables."""
        return settings.ec3_api_key or os.getenv("EC3_API_KEY")

    def _load_oauth_from_env(self) -> dict[str, Any] | None:
        """
        Load OAuth2 credentials from environment variables.

        Checks for:
        - EC3_OAUTH_CLIENT_ID
        - EC3_OAUTH_CLIENT_SECRET
        - EC3_OAUTH_USERNAME (for password grant)
        - EC3_OAUTH_PASSWORD (for password grant)
        - EC3_OAUTH_SCOPE (optional)
        - EC3_OAUTH_AUTHORIZATION_CODE (for code grant)

        Returns:
            OAuth config dict if credentials found, None otherwise
        """
        client_id = os.getenv("EC3_OAUTH_CLIENT_ID")
        client_secret = os.getenv("EC3_OAUTH_CLIENT_SECRET")

        if not client_id or not client_secret:
            return None

        # Check for password grant credentials
        username = os.getenv("EC3_OAUTH_USERNAME")
        password = os.getenv("EC3_OAUTH_PASSWORD")

        if username and password:
            return {
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "username": username,
                "password": password,
                "scope": os.getenv("EC3_OAUTH_SCOPE", "read"),
            }

        # Check for authorization code grant
        auth_code = os.getenv("EC3_OAUTH_AUTHORIZATION_CODE")
        if auth_code:
            return {
                "grant_type": "authorization_code",
                "client_id": client_id,
                "client_secret": client_secret,
                "code": auth_code,
            }

        return None

    async def __aenter__(self):
        headers = {}

        # If OAuth config provided, get access token
        if self.oauth_config:
            await self._get_oauth_token()
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
                logger.info("ec3_auth_mode", mode="oauth2", token_present=True)
            elif self.api_key:
                # OAuth failed but we have API key - use it as fallback
                headers["Authorization"] = f"Bearer {self.api_key}"
                logger.warning("ec3_auth_mode", mode="oauth2_failed_api_key_fallback",
                             message="OAuth2 token acquisition failed - falling back to API key")
            else:
                logger.error("ec3_auth_mode", mode="oauth2", token_present=False,
                           message="OAuth2 token acquisition failed and no API key available - using public access")
        # Otherwise use API key if provided
        elif self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            logger.info("ec3_auth_mode", mode="api_key", key_present=True)
        else:
            # No authentication - warn about limitations
            logger.warning(
                "ec3_no_authentication",
                message="No API key or OAuth config provided - using public access",
                limitations=[
                    "Rate limited to fewer requests per minute",
                    "Many endpoints will return 401 or 404",
                    "Limited data access",
                    "Public data only - no private/org-specific data"
                ],
                recommendation="Set EC3_API_KEY environment variable or provide oauth_config",
                get_key_url="https://buildingtransparency.org/ec3/manage-apps/keys",
            )

        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=60),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _get_oauth_token(self):
        """
        Get OAuth 2.0 access token using configured grant type.

        Supports:
        - Password (Resource Owner Password Credentials)
        - Authorization Code
        """
        if not self.oauth_config:
            return

        grant_type = self.oauth_config.get("grant_type")
        if grant_type not in ["password", "authorization_code"]:
            logger.error("Invalid grant_type. Must be 'password' or 'authorization_code'")
            return

        # Build token request payload
        payload = {
            "grant_type": grant_type,
            "client_id": self.oauth_config.get("client_id"),
            "client_secret": self.oauth_config.get("client_secret"),
        }

        if grant_type == "password":
            payload["username"] = self.oauth_config.get("username")
            payload["password"] = self.oauth_config.get("password")
        elif grant_type == "authorization_code":
            payload["code"] = self.oauth_config.get("code")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.OAUTH_TOKEN_URL,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data.get("access_token")
                        expires_in = data.get("expires_in", 3600)
                        self.token_expiry = time.time() + expires_in
                        logger.info("oauth_token_acquired", expires_in=expires_in)
                    else:
                        error_text = await response.text()
                        logger.error("oauth_token_failed", status=response.status, error=error_text)
        except Exception as e:
            logger.error("oauth_token_error", error=str(e))

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> tuple[int, Any]:
        """
        Make HTTP request with exponential backoff retry logic.

        Retries up to MAX_RETRIES times with delays: 2s, 4s, 8s, 16s

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments for aiohttp request

        Returns:
            Tuple of (status_code, response_data)
        """
        last_error = None

        for attempt in range(self.MAX_RETRIES + 1):
            try:
                async with self.session.request(method, url, **kwargs) as response:
                    status = response.status

                    # Check if token expired (401)
                    if status == 401 and self.oauth_config:
                        logger.info("Token expired, refreshing...")
                        await self._get_oauth_token()
                        if self.access_token:
                            # Update authorization header
                            if "headers" not in kwargs:
                                kwargs["headers"] = {}
                            kwargs["headers"]["Authorization"] = f"Bearer {self.access_token}"
                            # Retry with new token
                            continue

                    # Success
                    if status == 200:
                        try:
                            data = await response.json()
                            return (status, data)
                        except:
                            text = await response.text()
                            return (status, text)

                    # Client error (4xx) - don't retry
                    if 400 <= status < 500 and status != 429:
                        error_text = await response.text()
                        logger.error(
                            "ec3_client_error",
                            status=status,
                            error=error_text,
                            url=url,
                        )
                        return (status, None)

                    # Server error (5xx) or rate limit (429) - retry
                    if attempt < self.MAX_RETRIES:
                        delay = self.RETRY_DELAYS[attempt]
                        logger.warning(
                            "ec3_retry",
                            attempt=attempt + 1,
                            max_retries=self.MAX_RETRIES,
                            delay=delay,
                            status=status,
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        error_text = await response.text()
                        logger.error("ec3_max_retries_exceeded", status=status, error=error_text)
                        return (status, None)

            except aiohttp.ClientError as e:
                last_error = e
                if attempt < self.MAX_RETRIES:
                    delay = self.RETRY_DELAYS[attempt]
                    logger.warning(
                        "ec3_network_error_retry",
                        attempt=attempt + 1,
                        max_retries=self.MAX_RETRIES,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("ec3_network_error_final", error=str(e))
                    return (0, None)
            except Exception as e:
                logger.error("ec3_unexpected_error", error=str(e))
                return (0, None)

        # Should not reach here, but return error if it does
        return (0, None)

    async def search_epds(
        self,
        query: str = None,
        category: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search for EPDs in EC3 database.

        The EC3/OpenEPD API uses text search via the 'q' parameter.
        For material categories, use the category name as the query text.

        Args:
            query: Search query text (free text search)
            category: Material category (converted to text search)
            limit: Maximum results per page
            offset: Pagination offset

        Returns:
            API response with EPD list:
            {
                "count": total_count,
                "next": next_url,
                "previous": previous_url,
                "results": [...]
            }
        """
        params = {
            "limit": limit,
            "offset": offset,
        }

        # EC3 API uses 'q' parameter for text search
        # If category is provided, use it as the search query
        if category:
            params["q"] = category
        elif query:
            params["q"] = query

        url = f"{self.base_url}/epds"
        status, data = await self._request_with_retry("GET", url, params=params)

        if status == 200 and data:
            # Handle both dict and list responses from EC3 API
            if isinstance(data, dict):
                results = data.get("results", [])
                result_count = len(results)
            elif isinstance(data, list):
                results = data
                result_count = len(data)
                # Normalize to dict format for consistency
                data = {"results": data, "count": len(data), "next": None, "previous": None}
            else:
                results = []
                result_count = 0
                data = {"results": [], "count": 0, "next": None, "previous": None}

            logger.info(
                "ec3_search_success",
                query=query or category,
                results=result_count,
                total=data.get("count", result_count),
            )
            return data
        else:
            logger.error(
                "ec3_search_failed",
                status=status,
                query=query or category,
            )
            return {"results": [], "count": 0, "next": None, "previous": None}

    async def search_epds_all(
        self,
        query: str = None,
        category: str = None,
        max_results: int = None,
        batch_size: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Search for EPDs and automatically paginate through ALL results.

        This method follows the 'next' links in API responses to fetch
        all available data, not just one page.

        Args:
            query: Search query text
            category: Material category
            max_results: Maximum total results to fetch (None = unlimited)
            batch_size: Results per API request (default 1000)

        Returns:
            List of all EPD objects
        """
        all_results = []
        offset = 0
        total_fetched = 0

        logger.info(
            "ec3_search_all_start",
            query=query or category,
            max_results=max_results,
            batch_size=batch_size,
        )

        while True:
            # Determine how many to fetch in this batch
            if max_results:
                remaining = max_results - total_fetched
                if remaining <= 0:
                    break
                current_limit = min(batch_size, remaining)
            else:
                current_limit = batch_size

            # Fetch batch
            response = await self.search_epds(
                query=query,
                category=category,
                limit=current_limit,
                offset=offset,
            )

            results = response.get("results", [])
            if not results:
                # No more results
                break

            all_results.extend(results)
            total_fetched += len(results)

            logger.info(
                "ec3_search_all_progress",
                fetched=total_fetched,
                batch_size=len(results),
                total=response.get("count", "unknown"),
            )

            # Check if there's a next page
            next_url = response.get("next")
            if not next_url:
                # No more pages
                break

            # Update offset for next batch
            offset += len(results)

            # Safety check: if we got fewer results than requested, we're at the end
            if len(results) < current_limit:
                break

        logger.info(
            "ec3_search_all_complete",
            query=query or category,
            total_results=len(all_results),
        )

        return all_results

    async def validate_credentials(self) -> dict[str, Any]:
        """
        Validate EC3 API credentials by attempting to access a known endpoint.

        This should be called before starting large extraction operations to
        ensure credentials are valid and working.

        Returns:
            Dict with validation results:
            {
                "valid": True/False,
                "auth_method": "oauth2"/"api_key"/"none",
                "message": "description",
                "test_endpoint": "orgs",
                "test_result": {...}
            }
        """
        result = {
            "valid": False,
            "auth_method": "none",
            "message": "",
            "test_endpoint": "orgs",
            "test_result": None,
        }

        # Determine auth method
        if self.oauth_config:
            result["auth_method"] = "oauth2"
        elif self.api_key:
            result["auth_method"] = "api_key"
        else:
            result["auth_method"] = "none"
            result["message"] = "No authentication configured - using public access (limited)"
            logger.warning("ec3_no_auth_configured")
            return result

        # Test with a simple endpoint (orgs is usually accessible)
        try:
            response = await self.get_endpoint("orgs", limit=1)

            if "error" in response:
                error = response["error"]
                if error == "unauthorized":
                    result["valid"] = False
                    result["message"] = f"Authentication failed - credentials invalid or expired ({result['auth_method']})"
                    logger.error("ec3_credentials_invalid", auth_method=result["auth_method"])
                elif error == "not_found":
                    # Orgs endpoint not found is unusual but not auth failure
                    result["valid"] = True
                    result["message"] = f"Authentication appears valid ({result['auth_method']}) but test endpoint not accessible"
                    logger.warning("ec3_test_endpoint_not_found")
                else:
                    result["valid"] = False
                    result["message"] = f"Validation error: {error}"
                    logger.error("ec3_validation_error", error=error)
            else:
                # Success!
                result["valid"] = True
                result["message"] = f"Authentication valid ({result['auth_method']})"
                result["test_result"] = {
                    "count": response.get("count", 0),
                    "results_count": len(response.get("results", [])),
                }
                logger.info(
                    "ec3_credentials_valid",
                    auth_method=result["auth_method"],
                    test_count=result["test_result"]["count"],
                )
        except Exception as e:
            result["valid"] = False
            result["message"] = f"Validation exception: {str(e)}"
            logger.error("ec3_validation_exception", error=str(e))

        return result

    async def get_epd(self, epd_id: str) -> dict[str, Any] | None:
        """
        Get detailed EPD data by ID.

        Args:
            epd_id: OpenEPD ID or EC3 material ID

        Returns:
            EPD data dictionary
        """
        url = f"{self.base_url}/epds/{epd_id}"
        status, data = await self._request_with_retry("GET", url)

        if status == 200 and data:
            logger.info("ec3_epd_retrieved", epd_id=epd_id)
            return data
        else:
            logger.error("ec3_epd_not_found", epd_id=epd_id, status=status)
            return None

    async def get_materials(
        self,
        category: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get materials from EC3.

        Args:
            category: Material category (used as text search query)
            limit: Maximum results per page
            offset: Pagination offset

        Returns:
            API response with materials list:
            {
                "count": total_count,
                "next": next_url,
                "previous": previous_url,
                "results": [...]
            }
        """
        params = {"limit": limit, "offset": offset}
        if category:
            params["q"] = category  # Use text search for category

        url = f"{self.base_url}/materials"
        status, data = await self._request_with_retry("GET", url, params=params)

        if status == 200 and data:
            # Handle both dict and list responses from EC3 API
            if isinstance(data, dict):
                results = data.get("results", [])
            elif isinstance(data, list):
                results = data
                # Normalize to dict format
                data = {"results": data, "count": len(data), "next": None, "previous": None}
            else:
                results = []
                data = {"results": [], "count": 0, "next": None, "previous": None}

            logger.info("ec3_materials_retrieved", count=len(results))
            return data
        else:
            logger.error("ec3_materials_failed", status=status)
            return {"results": [], "count": 0, "next": None, "previous": None}

    async def get_plants(
        self,
        query: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get manufacturing plants from EC3.

        Args:
            query: Search query text
            limit: Maximum results per page
            offset: Pagination offset

        Returns:
            API response with plants list
        """
        params = {"limit": limit, "offset": offset}
        if query:
            params["q"] = query

        url = f"{self.base_url}/plants"
        status, data = await self._request_with_retry("GET", url, params=params)

        if status == 200 and data:
            # Normalize response format
            if isinstance(data, list):
                data = {"results": data, "count": len(data), "next": None, "previous": None}
            elif not isinstance(data, dict):
                data = {"results": [], "count": 0, "next": None, "previous": None}

            logger.info("ec3_plants_retrieved", count=len(data.get("results", [])))
            return data
        else:
            logger.error("ec3_plants_failed", status=status)
            return {"results": [], "count": 0, "next": None, "previous": None}

    async def get_projects(
        self,
        query: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get projects from EC3.

        Args:
            query: Search query text
            limit: Maximum results per page
            offset: Pagination offset

        Returns:
            API response with projects list
        """
        params = {"limit": limit, "offset": offset}
        if query:
            params["q"] = query

        url = f"{self.base_url}/projects"
        status, data = await self._request_with_retry("GET", url, params=params)

        if status == 200 and data:
            # Normalize response format
            if isinstance(data, list):
                data = {"results": data, "count": len(data), "next": None, "previous": None}
            elif not isinstance(data, dict):
                data = {"results": [], "count": 0, "next": None, "previous": None}

            logger.info("ec3_projects_retrieved", count=len(data.get("results", [])))
            return data
        else:
            logger.error("ec3_projects_failed", status=status)
            return {"results": [], "count": 0, "next": None, "previous": None}

    async def get_endpoint(
        self,
        endpoint: str,
        query: str = None,
        limit: int = 100,
        offset: int = 0,
        **extra_params,
    ) -> dict[str, Any]:
        """
        Generic method to fetch data from any EC3 API endpoint.

        This method provides a flexible way to query any endpoint in the EC3 API,
        including newly added endpoints or custom endpoints.

        Args:
            endpoint: Endpoint path (e.g., "users", "orgs", "pcrs", "baselines")
            query: Search query text (mapped to 'q' parameter)
            limit: Maximum results per page
            offset: Pagination offset
            **extra_params: Additional query parameters

        Returns:
            API response with normalized structure:
            {
                "count": total_count,
                "next": next_url,
                "previous": previous_url,
                "results": [...]
            }
        """
        params = {"limit": limit, "offset": offset}
        if query:
            params["q"] = query
        params.update(extra_params)

        # Clean endpoint path
        endpoint = endpoint.strip("/")
        url = f"{self.base_url}/{endpoint}"

        status, data = await self._request_with_retry("GET", url, params=params)

        if status == 200 and data:
            # Normalize response format
            if isinstance(data, list):
                data = {"results": data, "count": len(data), "next": None, "previous": None}
            elif not isinstance(data, dict):
                data = {"results": [], "count": 0, "next": None, "previous": None}

            logger.info(
                "ec3_endpoint_retrieved",
                endpoint=endpoint,
                count=len(data.get("results", [])),
                total=data.get("count", "unknown"),
            )
            return data
        elif status == 404:
            logger.warning(
                "ec3_endpoint_not_found",
                endpoint=endpoint,
                url=url,
                message="Endpoint does not exist or requires authentication",
            )
            return {"results": [], "count": 0, "next": None, "previous": None, "error": "not_found"}
        elif status == 401:
            logger.error(
                "ec3_authentication_error",
                endpoint=endpoint,
                message="Authentication required or token expired",
            )
            return {"results": [], "count": 0, "next": None, "previous": None, "error": "unauthorized"}
        elif status == 429:
            logger.error(
                "ec3_rate_limited",
                endpoint=endpoint,
                message="Rate limit exceeded - retries exhausted",
            )
            return {"results": [], "count": 0, "next": None, "previous": None, "error": "rate_limited"}
        else:
            logger.error(
                "ec3_endpoint_failed",
                endpoint=endpoint,
                status=status,
            )
            return {"results": [], "count": 0, "next": None, "previous": None, "error": f"status_{status}"}

    async def extract_all_data(
        self,
        endpoints: list[str] = None,
        max_per_endpoint: int = None,
        validate_auth: bool = True,
        stop_on_auth_failure: bool = True,
    ) -> dict[str, Any]:
        """
        Extract data from multiple EC3 API endpoints with comprehensive coverage.

        This method supports ALL official EC3 API endpoints as documented at:
        https://buildingtransparency.org/ec3/manage-apps/api-doc/api

        IMPORTANT: This method requires valid authentication (OAuth2 or API key).
        Most endpoints will return 401 Unauthorized without proper credentials.

        Args:
            endpoints: List of endpoints to extract. If None, uses comprehensive default list.
            max_per_endpoint: Maximum results per endpoint (None = unlimited)
            validate_auth: Validate credentials before starting extraction (default: True)
            stop_on_auth_failure: Stop extraction if credentials are invalid (default: True)

        Returns:
            Dictionary with extraction results and statistics:
            {
                "auth_validation": {
                    "valid": True/False,
                    "auth_method": "oauth2"/"api_key"/"none",
                    "message": "..."
                },
                "data": {
                    "epds": [...],
                    "materials": [...],
                    ...
                },
                "stats": {
                    "epds": {"count": 100, "status": "success"},
                    "materials": {"count": 50, "status": "success"},
                    ...
                },
                "summary": {
                    "total_endpoints": 10,
                    "successful": 8,
                    "failed": 2,
                    "total_records": 1500
                }
            }
        """
        # Comprehensive list of all EC3 API endpoints
        if endpoints is None:
            endpoints = [
                # Core endpoints (most commonly used)
                "epds",
                "materials",
                "plants",
                "projects",

                # User and organization management
                "users",
                "user_groups",
                "orgs",
                "plant_groups",

                # EPD-related endpoints
                "epd_requests",
                "epd_imports",
                "industry_epds",
                "generic_estimates",

                # Standards and reference data
                "pcrs",  # Product Category Rules
                "baselines",
                "reference_sets",
                "categories",
                "standards",

                # Project-related endpoints
                "civil_projects",
                "collections",
                "building_groups",
                "building_campuses",
                "building_complexes",
                "project_views",
                "bim_projects",
                "elements",

                # Integrations
                "procore",
                "autodesk_takeoff",
                "bid_leveling_sheets",
                "tally_projects",

                # Additional endpoints
                "charts",
                "dashboard",
                "docs",
                "access_management",
                "configurations",
                "jobs",
            ]

        results = {
            "auth_validation": None,
            "data": {},
            "stats": {},
            "summary": {
                "total_endpoints": len(endpoints),
                "successful": 0,
                "failed": 0,
                "not_found": 0,
                "unauthorized": 0,
                "total_records": 0,
                "stopped_early": False,
                "stop_reason": None,
            }
        }

        # Validate credentials before starting
        if validate_auth:
            logger.info("ec3_validating_credentials")
            auth_result = await self.validate_credentials()
            results["auth_validation"] = auth_result

            if not auth_result["valid"] and stop_on_auth_failure:
                logger.error(
                    "ec3_auth_validation_failed",
                    message=auth_result["message"],
                    auth_method=auth_result["auth_method"],
                )
                results["summary"]["stopped_early"] = True
                results["summary"]["stop_reason"] = "authentication_failed"
                return results
            elif not auth_result["valid"]:
                logger.warning(
                    "ec3_auth_validation_failed_continue",
                    message=auth_result["message"],
                    note="Continuing extraction anyway - expect many 401 errors",
                )

        logger.info(
            "ec3_extract_all_start",
            endpoints=len(endpoints),
            endpoint_list=endpoints,
            max_per_endpoint=max_per_endpoint,
            auth_validated=validate_auth,
        )

        for endpoint in endpoints:
            logger.info("ec3_extract_endpoint_start", endpoint=endpoint)

            try:
                if endpoint == "epds":
                    # EPDs - use specialized search method
                    data = await self.search_epds_all(max_results=max_per_endpoint)
                    results["data"][endpoint] = data
                    results["stats"][endpoint] = {
                        "count": len(data),
                        "status": "success",
                    }
                    results["summary"]["successful"] += 1
                    results["summary"]["total_records"] += len(data)
                elif endpoint in ["materials", "plants", "projects"]:
                    # Use specialized methods for these endpoints
                    method_map = {
                        "materials": self.get_materials,
                        "plants": self.get_plants,
                        "projects": self.get_projects,
                    }
                    data = await self._paginate_all(
                        method_map[endpoint],
                        max_results=max_per_endpoint,
                    )
                    results["data"][endpoint] = data
                    results["stats"][endpoint] = {
                        "count": len(data),
                        "status": "success",
                    }
                    results["summary"]["successful"] += 1
                    results["summary"]["total_records"] += len(data)
                else:
                    # Use generic endpoint method for all other endpoints
                    response = await self.get_endpoint(endpoint, limit=1000)

                    # Check for errors
                    if "error" in response:
                        error_type = response["error"]
                        results["stats"][endpoint] = {
                            "count": 0,
                            "status": "failed",
                            "error": error_type,
                        }
                        results["summary"]["failed"] += 1

                        if error_type == "not_found":
                            results["summary"]["not_found"] += 1
                        elif error_type == "unauthorized":
                            results["summary"]["unauthorized"] += 1
                    else:
                        # Paginate through all results
                        data = await self._paginate_all_generic(
                            endpoint,
                            max_results=max_per_endpoint,
                        )
                        results["data"][endpoint] = data
                        results["stats"][endpoint] = {
                            "count": len(data),
                            "status": "success",
                        }
                        results["summary"]["successful"] += 1
                        results["summary"]["total_records"] += len(data)

                logger.info(
                    "ec3_extract_endpoint_complete",
                    endpoint=endpoint,
                    count=results["stats"][endpoint]["count"],
                    status=results["stats"][endpoint]["status"],
                )

            except Exception as e:
                logger.error(
                    "ec3_extract_endpoint_error",
                    endpoint=endpoint,
                    error=str(e),
                )
                results["stats"][endpoint] = {
                    "count": 0,
                    "status": "error",
                    "error": str(e),
                }
                results["summary"]["failed"] += 1

        # Log final summary
        logger.info(
            "ec3_extract_all_complete",
            total_endpoints=results["summary"]["total_endpoints"],
            successful=results["summary"]["successful"],
            failed=results["summary"]["failed"],
            not_found=results["summary"]["not_found"],
            unauthorized=results["summary"]["unauthorized"],
            total_records=results["summary"]["total_records"],
        )

        return results

    async def _paginate_all(
        self,
        fetch_func,
        max_results: int = None,
        batch_size: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Helper method to paginate through all results from an endpoint.

        Args:
            fetch_func: Function to call for fetching (e.g., self.get_materials)
            max_results: Maximum total results
            batch_size: Results per request

        Returns:
            List of all objects
        """
        all_results = []
        offset = 0
        total_fetched = 0

        while True:
            # Determine batch size
            if max_results:
                remaining = max_results - total_fetched
                if remaining <= 0:
                    break
                current_limit = min(batch_size, remaining)
            else:
                current_limit = batch_size

            # Fetch batch
            response = await fetch_func(limit=current_limit, offset=offset)
            results = response.get("results", [])

            if not results:
                break

            all_results.extend(results)
            total_fetched += len(results)

            # Check for next page
            if not response.get("next"):
                break

            offset += len(results)

            # Safety check
            if len(results) < current_limit:
                break

        return all_results

    async def _paginate_all_generic(
        self,
        endpoint: str,
        max_results: int = None,
        batch_size: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Helper method to paginate through all results from a generic endpoint.

        Args:
            endpoint: Endpoint path (e.g., "users", "orgs", "pcrs")
            max_results: Maximum total results
            batch_size: Results per request

        Returns:
            List of all objects from the endpoint
        """
        all_results = []
        offset = 0
        total_fetched = 0

        while True:
            # Determine batch size
            if max_results:
                remaining = max_results - total_fetched
                if remaining <= 0:
                    break
                current_limit = min(batch_size, remaining)
            else:
                current_limit = batch_size

            # Fetch batch
            response = await self.get_endpoint(
                endpoint,
                limit=current_limit,
                offset=offset,
            )

            # Check for errors
            if "error" in response:
                break

            results = response.get("results", [])

            if not results:
                break

            all_results.extend(results)
            total_fetched += len(results)

            # Check for next page
            if not response.get("next"):
                break

            offset += len(results)

            # Safety check
            if len(results) < current_limit:
                break

        return all_results


class EC3EPDParser:
    """Parse EC3/openEPD data into MOTHRA entities."""

    def __init__(self):
        self.category_mapping = {
            # EC3 categories to MOTHRA taxonomy
            "Concrete": ["material", "construction", "concrete"],
            "Steel": ["material", "construction", "steel"],
            "Wood": ["material", "construction", "wood", "biomass"],
            "Insulation": ["material", "construction", "insulation"],
            "Glass": ["material", "construction", "glass"],
            "Aluminum": ["material", "construction", "aluminum", "metal"],
            "Brick": ["material", "construction", "brick"],
            "Gypsum": ["material", "construction", "gypsum"],
        }

    def parse_epd_to_entity(
        self, epd_data: dict[str, Any], source: DataSource
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Parse EPD data into CarbonEntity and verification data.

        Args:
            epd_data: Raw EPD data from EC3 API
            source: DataSource record

        Returns:
            Tuple of (entity_dict, verification_dict)
        """
        # Extract basic info
        name = epd_data.get("name", "Unknown EPD")
        description = epd_data.get("description", "")
        manufacturer = epd_data.get("manufacturer", {}).get("name", "Unknown")

        # Category and taxonomy
        category = epd_data.get("category", "")
        taxonomy_categories = self.category_mapping.get(
            category, ["material", "construction"]
        )

        # Geographic scope
        geographic_scope = []
        if "geography" in epd_data:
            geo = epd_data["geography"]
            if isinstance(geo, dict):
                country = geo.get("country")
                if country:
                    geographic_scope.append(country)
            elif isinstance(geo, list):
                geographic_scope.extend(geo)

        # Build entity dict
        entity = {
            "name": f"{manufacturer} - {name}"[:500],
            "description": description[:2000] or f"EPD for {name} from EC3",
            "source_id": source.name,
            "source_uuid": source.id,
            "entity_type": "material",
            "category_hierarchy": taxonomy_categories,
            "geographic_scope": geographic_scope or ["Global"],
            "quality_score": 0.95,  # High quality - verified EPD
            "custom_tags": ["epd", "verified", "ec3", category.lower()],
            "raw_data": epd_data,
            "extra_metadata": {
                "manufacturer": manufacturer,
                "ec3_category": category,
            },
        }

        # Build verification dict
        verification = self._parse_verification_data(epd_data)

        return entity, verification

    def _parse_verification_data(self, epd_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract comprehensive verification data from EPD.

        Extracts 40+ fields including:
        - GHG emissions (total, by gas type, by LCA stage, biogenic)
        - Additional environmental indicators (acidification, eutrophication, etc.)
        - Manufacturing and plant details
        - Material composition (recycled content, renewable materials)
        - Temporal and geographic validity
        - Data quality indicators
        - PCR and methodology details
        - Compliance and certification info
        - Product specifications
        """

        # ========================================
        # 1. GWP DATA (Primary carbon metric)
        # ========================================
        gwp_data = epd_data.get("gwp", {})
        if isinstance(gwp_data, dict):
            gwp_total = gwp_data.get("total") or gwp_data.get("value")
            gwp_co2 = gwp_data.get("co2")
            gwp_ch4 = gwp_data.get("ch4")
            gwp_n2o = gwp_data.get("n2o")
        elif isinstance(gwp_data, (int, float)):
            gwp_total = gwp_data
            gwp_co2 = None
            gwp_ch4 = None
            gwp_n2o = None
        else:
            gwp_total = None
            gwp_co2 = None
            gwp_ch4 = None
            gwp_n2o = None

        gwp_biogenic = epd_data.get("gwp_biogenic")
        gwp_fossil = epd_data.get("gwp_fossil")
        gwp_luluc = epd_data.get("gwp_luluc")  # Land use/land use change

        # ========================================
        # 2. LCA STAGES (EN 15804 lifecycle)
        # ========================================
        lca_stages_data = epd_data.get("lca_stages", {})
        lca_stages_included = []
        lca_stage_emissions = {}

        if isinstance(lca_stages_data, dict):
            for stage_key, stage_value in lca_stages_data.items():
                if stage_value is not None:
                    stage_upper = stage_key.upper()
                    lca_stages_included.append(stage_upper)
                    lca_stage_emissions[stage_upper] = stage_value

        # ========================================
        # 3. ADDITIONAL ENVIRONMENTAL INDICATORS
        # ========================================
        # These are critical for verifiers beyond just carbon
        env_indicators = {}

        # Acidification Potential (AP)
        ap_data = epd_data.get("ap") or epd_data.get("acidification")
        if ap_data:
            env_indicators["acidification_potential"] = ap_data

        # Eutrophication Potential (EP)
        ep_data = epd_data.get("ep") or epd_data.get("eutrophication")
        if ep_data:
            env_indicators["eutrophication_potential"] = ep_data

        # Ozone Depletion Potential (ODP)
        odp_data = epd_data.get("odp") or epd_data.get("ozone_depletion")
        if odp_data:
            env_indicators["ozone_depletion_potential"] = odp_data

        # Photochemical Ozone Creation Potential (POCP) / Smog
        pocp_data = epd_data.get("pocp") or epd_data.get("smog")
        if pocp_data:
            env_indicators["smog_formation_potential"] = pocp_data

        # Abiotic Depletion Potential (ADP) - elements and fossil
        adp_elements = epd_data.get("adp_elements") or epd_data.get("adp_minerals")
        if adp_elements:
            env_indicators["abiotic_depletion_elements"] = adp_elements

        adp_fossil = epd_data.get("adp_fossil") or epd_data.get("adp_energy")
        if adp_fossil:
            env_indicators["abiotic_depletion_fossil"] = adp_fossil

        # Water use
        water_use = epd_data.get("water_use") or epd_data.get("water_depletion")
        if water_use:
            env_indicators["water_use"] = water_use

        # Land use
        land_use = epd_data.get("land_use")
        if land_use:
            env_indicators["land_use"] = land_use

        # Primary energy demand
        ped_renewable = epd_data.get("ped_renewable") or epd_data.get("primary_energy_renewable")
        ped_nonrenewable = epd_data.get("ped_nonrenewable") or epd_data.get("primary_energy_nonrenewable")
        if ped_renewable:
            env_indicators["primary_energy_renewable"] = ped_renewable
        if ped_nonrenewable:
            env_indicators["primary_energy_nonrenewable"] = ped_nonrenewable

        # ========================================
        # 4. MATERIAL COMPOSITION (Verifiers need this!)
        # ========================================
        material_composition = {}

        # Recycled content
        recycled_content = epd_data.get("recycled_content") or epd_data.get("post_consumer_recycled_content")
        if recycled_content is not None:
            material_composition["recycled_content_percent"] = recycled_content

        post_consumer = epd_data.get("post_consumer_content")
        if post_consumer is not None:
            material_composition["post_consumer_percent"] = post_consumer

        pre_consumer = epd_data.get("pre_consumer_content")
        if pre_consumer is not None:
            material_composition["pre_consumer_percent"] = pre_consumer

        # Renewable materials
        renewable_content = epd_data.get("renewable_content") or epd_data.get("bio_based_content")
        if renewable_content is not None:
            material_composition["renewable_content_percent"] = renewable_content

        # Rapidly renewable
        rapidly_renewable = epd_data.get("rapidly_renewable_content")
        if rapidly_renewable is not None:
            material_composition["rapidly_renewable_percent"] = rapidly_renewable

        # ========================================
        # 5. MANUFACTURING & PLANT DETAILS
        # ========================================
        manufacturing_data = {}

        # Plant/factory information
        plant_data = epd_data.get("plant") or epd_data.get("manufacturing_plant")
        if plant_data and isinstance(plant_data, dict):
            manufacturing_data["plant_name"] = plant_data.get("name")
            manufacturing_data["plant_location"] = plant_data.get("location")
            manufacturing_data["plant_country"] = plant_data.get("country")

        # Manufacturing process
        manufacturing_process = epd_data.get("manufacturing_process")
        if manufacturing_process:
            manufacturing_data["manufacturing_process"] = manufacturing_process

        # ========================================
        # 6. DECLARED UNITS & FUNCTIONAL UNITS
        # ========================================
        declared_unit = epd_data.get("declared_unit", "1 kg")
        functional_unit = epd_data.get("functional_unit")
        reference_service_life = epd_data.get("reference_service_life") or epd_data.get("rsl")

        # Mass per declared unit (for normalization)
        mass_per_unit = epd_data.get("mass_per_declared_unit")

        # ========================================
        # 7. EPD METADATA & REGISTRATION
        # ========================================
        epd_id = epd_data.get("id") or epd_data.get("openepd_id")
        epd_number = epd_data.get("epd_number") or epd_data.get("registration_number")
        epd_version = epd_data.get("version")

        # Program operator
        program_operator = epd_data.get("program_operator", {})
        if isinstance(program_operator, dict):
            program_operator_name = program_operator.get("name")
        else:
            program_operator_name = str(program_operator) if program_operator else None

        # ========================================
        # 8. TEMPORAL VALIDITY (Critical for verifiers!)
        # ========================================
        # Publication date
        published_date = epd_data.get("published_date") or epd_data.get("publication_date")
        if published_date:
            try:
                published_date = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            except:
                published_date = None

        # Valid from date
        valid_from = epd_data.get("valid_from")
        if valid_from:
            try:
                valid_from = datetime.fromisoformat(valid_from.replace("Z", "+00:00"))
            except:
                valid_from = None

        # Valid until date (expiry)
        valid_until = epd_data.get("valid_until")
        if valid_until:
            try:
                expiry_date = datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
            except:
                expiry_date = None
        else:
            expiry_date = None

        # ========================================
        # 9. GEOGRAPHIC VALIDITY
        # ========================================
        geographic_scope = []
        if "geography" in epd_data:
            geo = epd_data["geography"]
            if isinstance(geo, dict):
                country = geo.get("country")
                region = geo.get("region")
                if country:
                    geographic_scope.append(country)
                if region:
                    geographic_scope.append(region)
            elif isinstance(geo, list):
                geographic_scope.extend(geo)
            elif isinstance(geo, str):
                geographic_scope.append(geo)

        # ========================================
        # 10. PCR (Product Category Rules) DETAILS
        # ========================================
        pcr_reference = epd_data.get("pcr") or epd_data.get("pcr_reference")
        pcr_version = epd_data.get("pcr_version")
        pcr_publisher = epd_data.get("pcr_publisher")

        # ========================================
        # 11. VERIFICATION BODY & STANDARDS
        # ========================================
        third_party_verified = epd_data.get("third_party_verified", True)
        verifier = epd_data.get("verifier") or epd_data.get("verification_body")
        verification_date = epd_data.get("verification_date")
        if verification_date:
            try:
                verification_date = datetime.fromisoformat(verification_date.replace("Z", "+00:00"))
            except:
                verification_date = None

        # Compliance flags
        iso_14067_compliant = epd_data.get("iso_14067_compliant", True)
        en_15804_compliant = epd_data.get("en_15804_compliant", True)
        iso_21930_compliant = epd_data.get("iso_21930_compliant", False)

        # ========================================
        # 12. DATA QUALITY INDICATORS (ISO 14044)
        # ========================================
        data_quality = {}

        # Temporal coverage
        temporal_coverage = epd_data.get("temporal_coverage")
        if temporal_coverage:
            data_quality["temporal_coverage"] = temporal_coverage

        # Geographic coverage
        geographic_coverage = epd_data.get("geographic_coverage")
        if geographic_coverage:
            data_quality["geographic_coverage"] = geographic_coverage

        # Technological coverage
        technological_coverage = epd_data.get("technological_coverage")
        if technological_coverage:
            data_quality["technological_coverage"] = technological_coverage

        # Data quality rating
        data_quality_rating = epd_data.get("data_quality_rating")
        if data_quality_rating:
            data_quality["data_quality_rating"] = data_quality_rating

        # ========================================
        # 13. LCA METHODOLOGY
        # ========================================
        lca_methodology = {}

        # LCA software used
        lca_software = epd_data.get("lca_software")
        if lca_software:
            lca_methodology["lca_software"] = lca_software

        # Database version (e.g., ecoinvent 3.8)
        database_version = epd_data.get("database_version") or epd_data.get("lca_database")
        if database_version:
            lca_methodology["database_version"] = database_version

        # Cut-off rules
        cutoff_rules = epd_data.get("cutoff_rules")
        if cutoff_rules:
            lca_methodology["cutoff_rules"] = cutoff_rules

        # Allocation method
        allocation_method = epd_data.get("allocation_method")
        if allocation_method:
            lca_methodology["allocation_method"] = allocation_method

        # ========================================
        # 14. SCENARIOS & ASSUMPTIONS
        # ========================================
        scenarios = {}

        # Transport scenario
        transport_distance = epd_data.get("transport_distance")
        if transport_distance:
            scenarios["transport_distance_km"] = transport_distance

        transport_mode = epd_data.get("transport_mode")
        if transport_mode:
            scenarios["transport_mode"] = transport_mode

        # Installation scenario
        installation_scenario = epd_data.get("installation_scenario")
        if installation_scenario:
            scenarios["installation_scenario"] = installation_scenario

        # End-of-life scenario
        eol_scenario = epd_data.get("end_of_life_scenario") or epd_data.get("eol_scenario")
        if eol_scenario:
            scenarios["end_of_life_scenario"] = eol_scenario

        # ========================================
        # 15. PRODUCT SPECIFICATIONS
        # ========================================
        product_specs = {}

        # Physical properties
        density = epd_data.get("density")
        if density:
            product_specs["density"] = density

        thickness = epd_data.get("thickness")
        if thickness:
            product_specs["thickness"] = thickness

        # Performance properties
        compressive_strength = epd_data.get("compressive_strength")
        if compressive_strength:
            product_specs["compressive_strength"] = compressive_strength

        thermal_conductivity = epd_data.get("thermal_conductivity") or epd_data.get("r_value")
        if thermal_conductivity:
            product_specs["thermal_conductivity"] = thermal_conductivity

        # ========================================
        # BUILD VERIFICATION RECORD
        # ========================================
        verification = {
            # GHG & Carbon (Primary metrics)
            "ghg_scopes": [GHGScope.SCOPE_1.value, GHGScope.SCOPE_3.value],
            "gwp_total": gwp_total,
            "gwp_co2": gwp_co2,
            "gwp_ch4": gwp_ch4,
            "gwp_n2o": gwp_n2o,
            "gwp_biogenic": gwp_biogenic,
            "gwp_fossil": gwp_fossil,
            "gwp_luluc": gwp_luluc,

            # LCA Stages
            "lca_stages_included": lca_stages_included,
            "lca_stage_emissions": lca_stage_emissions,

            # Units
            "declared_unit": declared_unit,
            "functional_unit": functional_unit,
            "reference_service_life": reference_service_life,

            # EPD Registration
            "epd_registration_number": epd_number,
            "epd_version": epd_version,
            "epd_program_operator": program_operator_name,
            "openepd_id": epd_id,
            "ec3_material_id": epd_data.get("material_id"),

            # PCR
            "pcr_reference": pcr_reference,
            "pcr_version": pcr_version,
            "pcr_publisher": pcr_publisher,

            # Temporal Validity
            "published_date": published_date,
            "valid_from_date": valid_from,
            "expiry_date": expiry_date,

            # Verification
            "verification_status": (
                VerificationStatus.VERIFIED.value
                if third_party_verified
                else VerificationStatus.PENDING.value
            ),
            "verification_standards": [
                VerificationStandard.EN_15804.value,
                VerificationStandard.ISO_14067.value,
            ],
            "verification_body": verifier,
            "verification_date": verification_date,
            "third_party_verified": third_party_verified,

            # Compliance
            "iso_14067_compliant": iso_14067_compliant,
            "en_15804_compliant": en_15804_compliant,
            "iso_21930_compliant": iso_21930_compliant,

            # Document
            "document_url": epd_data.get("document_url") or epd_data.get("url"),

            # Store all additional data in metadata
            "verification_metadata": {
                "source": "EC3/Building Transparency",
                "import_date": datetime.now(UTC).isoformat(),

                # Environmental indicators (15+ indicators)
                "environmental_indicators": env_indicators,

                # Material composition (recycled/renewable content)
                "material_composition": material_composition,

                # Manufacturing details
                "manufacturing": manufacturing_data,

                # Geographic scope
                "geographic_scope": geographic_scope,

                # Data quality indicators
                "data_quality": data_quality,

                # LCA methodology
                "lca_methodology": lca_methodology,

                # Scenarios and assumptions
                "scenarios": scenarios,

                # Product specifications
                "product_specifications": product_specs,

                # Store original EPD data for full traceability
                "raw_epd_summary": {
                    "name": epd_data.get("name"),
                    "manufacturer": epd_data.get("manufacturer", {}).get("name") if isinstance(epd_data.get("manufacturer"), dict) else str(epd_data.get("manufacturer")),
                    "category": epd_data.get("category"),
                    "mass_per_unit": mass_per_unit,
                },
            },
        }

        return verification


async def import_epds_from_ec3(
    category: str = None, limit: int = 100
) -> dict[str, Any]:
    """
    Import EPDs from EC3 into MOTHRA database.

    Args:
        category: Material category filter
        limit: Maximum EPDs to import

    Returns:
        Import statistics
    """
    # Register EC3 as data source
    async with get_db_context() as db:
        from sqlalchemy import select

        stmt = select(DataSource).where(DataSource.name == "EC3 Building Transparency")
        result = await db.execute(stmt)
        source = result.scalar_one_or_none()

        if not source:
            source = DataSource(
                name="EC3 Building Transparency",
                source_type="epd_database",
                category="standards",  # EPD standards organization
                url="https://buildingtransparency.org/ec3/",
                access_method="api",
                update_frequency="continuous",
                extra_metadata={
                    "api_endpoint": "https://openepd.buildingtransparency.org/api",
                    "database_size": "90000+ EPDs",
                },
            )
            db.add(source)
            await db.commit()
            await db.refresh(source)

    # Fetch EPDs
    async with EC3Client() as client:
        epd_results = await client.search_epds(category=category, limit=limit)

    # Handle both dict and list responses
    if isinstance(epd_results, dict):
        epds = epd_results.get("results", [])
    elif isinstance(epd_results, list):
        epds = epd_results
    else:
        epds = []

    if not epds:
        logger.warning("no_epds_found", category=category)
        return {
            "epds_imported": 0,
            "errors": 0,
            "category": category,
        }

    # Parse and store
    parser = EC3EPDParser()
    imported = 0
    errors = 0

    async with get_db_context() as db:
        for epd_data in epds:
            try:
                # Parse EPD
                entity_dict, verification_dict = parser.parse_epd_to_entity(
                    epd_data, source
                )

                # Create entity
                entity = CarbonEntity(**entity_dict)
                db.add(entity)
                await db.flush()

                # Create verification record
                verification_dict["entity_id"] = entity.id
                verification = CarbonEntityVerification(**verification_dict)
                db.add(verification)

                imported += 1

                if imported % 10 == 0:
                    await db.commit()
                    logger.info("ec3_import_progress", imported=imported, total=len(epds))

            except Exception as e:
                errors += 1
                logger.error(
                    "ec3_import_error",
                    epd_name=epd_data.get("name"),
                    error=str(e),
                )

        await db.commit()

    logger.info(
        "ec3_import_complete",
        imported=imported,
        errors=errors,
        category=category,
    )

    return {
        "epds_imported": imported,
        "errors": errors,
        "category": category,
    }


async def main():
    """Example usage."""
    print("EC3 Integration - Example")

    # Test API connection
    async with EC3Client() as client:
        # Search for concrete EPDs
        results = await client.search_epds(category="Concrete", limit=10)
        print(f"Found {results.get('count', 0)} concrete EPDs")

        # Import sample
        stats = await import_epds_from_ec3(category="Concrete", limit=10)
        print(f"Imported: {stats['epds_imported']}, Errors: {stats['errors']}")


if __name__ == "__main__":
    asyncio.run(main())
