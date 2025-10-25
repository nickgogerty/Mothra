"""
EC3 (Embodied Carbon in Construction Calculator) Integration.

Connects to Building Transparency's openEPD API to fetch:
- 90,000+ digital EPDs
- Construction material carbon footprints
- Verified environmental product declarations
- LCA data with full EN 15804 compliance

API: https://openepd.buildingtransparency.org/api
Docs: https://docs.buildingtransparency.org/
"""

import asyncio
import os
from datetime import UTC, datetime
from typing import Any
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
    Client for EC3/openEPD API.

    Requires API key from https://buildingtransparency.org/ec3/manage-apps/keys
    """

    BASE_URL = "https://openepd.buildingtransparency.org/api"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("EC3_API_KEY")
        self.session = None

    async def __aenter__(self):
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=60),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def search_epds(
        self,
        query: str = None,
        category: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Search for EPDs in EC3 database.

        Args:
            query: Search query text
            category: Material category filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            API response with EPD list
        """
        params = {
            "limit": limit,
            "offset": offset,
        }

        if query:
            params["q"] = query
        if category:
            params["category"] = category

        try:
            url = f"{self.BASE_URL}/epds"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        "ec3_search_success",
                        query=query,
                        results=len(data.get("results", [])),
                    )
                    return data
                else:
                    error_text = await response.text()
                    logger.error(
                        "ec3_search_failed",
                        status=response.status,
                        error=error_text,
                    )
                    return {"results": [], "count": 0}

        except Exception as e:
            logger.error("ec3_api_error", error=str(e))
            return {"results": [], "count": 0}

    async def get_epd(self, epd_id: str) -> dict[str, Any] | None:
        """
        Get detailed EPD data by ID.

        Args:
            epd_id: OpenEPD ID or EC3 material ID

        Returns:
            EPD data dictionary
        """
        try:
            url = f"{self.BASE_URL}/epds/{epd_id}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("ec3_epd_retrieved", epd_id=epd_id)
                    return data
                else:
                    logger.error(
                        "ec3_epd_not_found",
                        epd_id=epd_id,
                        status=response.status,
                    )
                    return None

        except Exception as e:
            logger.error("ec3_get_epd_error", epd_id=epd_id, error=str(e))
            return None

    async def get_materials(
        self,
        category: str = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get materials from EC3.

        Args:
            category: Material category filter
            limit: Maximum results

        Returns:
            List of materials
        """
        params = {"limit": limit}
        if category:
            params["category"] = category

        try:
            url = f"{self.BASE_URL}/materials"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(
                        "ec3_materials_retrieved",
                        count=len(data.get("results", [])),
                    )
                    return data.get("results", [])
                else:
                    logger.error("ec3_materials_failed", status=response.status)
                    return []

        except Exception as e:
            logger.error("ec3_materials_error", error=str(e))
            return []


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
        """Extract verification data from EPD."""

        # Get GWP data
        gwp_data = epd_data.get("gwp", {})
        if isinstance(gwp_data, dict):
            gwp_total = gwp_data.get("total")
        elif isinstance(gwp_data, (int, float)):
            gwp_total = gwp_data
        else:
            gwp_total = None

        # Get LCA stages
        lca_stages_data = epd_data.get("lca_stages", {})
        lca_stages_included = []
        lca_stage_emissions = {}

        if isinstance(lca_stages_data, dict):
            for stage_key, stage_value in lca_stages_data.items():
                if stage_value is not None:
                    lca_stages_included.append(stage_key.upper())
                    lca_stage_emissions[stage_key.upper()] = stage_value

        # Get declared unit
        declared_unit = epd_data.get("declared_unit", "1 kg")

        # Get EPD metadata
        epd_id = epd_data.get("id") or epd_data.get("openepd_id")
        program_operator = epd_data.get("program_operator", {})
        if isinstance(program_operator, dict):
            program_operator_name = program_operator.get("name")
        else:
            program_operator_name = str(program_operator) if program_operator else None

        # Get validity period
        valid_until = epd_data.get("valid_until")
        if valid_until:
            try:
                expiry_date = datetime.fromisoformat(
                    valid_until.replace("Z", "+00:00")
                )
            except:
                expiry_date = None
        else:
            expiry_date = None

        # Get verification info
        third_party_verified = epd_data.get("third_party_verified", True)

        verification = {
            "ghg_scopes": [GHGScope.SCOPE_1.value, GHGScope.SCOPE_3.value],
            "lca_stages_included": lca_stages_included,
            "lca_stage_emissions": lca_stage_emissions,
            "epd_registration_number": epd_data.get("epd_number"),
            "epd_program_operator": program_operator_name,
            "pcr_reference": epd_data.get("pcr"),
            "declared_unit": declared_unit,
            "functional_unit": epd_data.get("functional_unit"),
            "reference_service_life": epd_data.get("reference_service_life"),
            "gwp_total": gwp_total,
            "gwp_biogenic": epd_data.get("gwp_biogenic"),
            "verification_status": (
                VerificationStatus.VERIFIED.value
                if third_party_verified
                else VerificationStatus.PENDING.value
            ),
            "verification_standards": [
                VerificationStandard.EN_15804.value,
                VerificationStandard.ISO_14067.value,
            ],
            "verification_body": epd_data.get("verifier"),
            "expiry_date": expiry_date,
            "ec3_material_id": epd_data.get("material_id"),
            "openepd_id": epd_id,
            "iso_14067_compliant": True,
            "en_15804_compliant": True,
            "third_party_verified": third_party_verified,
            "document_url": epd_data.get("document_url") or epd_data.get("url"),
            "verification_metadata": {
                "source": "EC3/Building Transparency",
                "import_date": datetime.now(UTC).isoformat(),
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

    epds = epd_results.get("results", [])

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
