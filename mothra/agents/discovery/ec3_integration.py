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
        self.api_key = api_key or settings.ec3_api_key or os.getenv("EC3_API_KEY")
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

        The EC3/OpenEPD API uses text search via the 'q' parameter.
        For material categories, use the category name as the query text.

        Args:
            query: Search query text (free text search)
            category: Material category (converted to text search)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            API response with EPD list
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

        try:
            url = f"{self.BASE_URL}/epds"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Handle both dict and list responses from EC3 API
                    if isinstance(data, dict):
                        results = data.get("results", [])
                        result_count = len(results)
                    elif isinstance(data, list):
                        results = data
                        result_count = len(data)
                        # Normalize to dict format for consistency
                        data = {"results": data, "count": len(data)}
                    else:
                        results = []
                        result_count = 0
                        data = {"results": [], "count": 0}

                    logger.info(
                        "ec3_search_success",
                        query=query,
                        results=result_count,
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
            category: Material category (used as text search query)
            limit: Maximum results

        Returns:
            List of materials
        """
        params = {"limit": limit}
        if category:
            params["q"] = category  # Use text search for category

        try:
            url = f"{self.BASE_URL}/materials"
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()

                    # Handle both dict and list responses from EC3 API
                    if isinstance(data, dict):
                        results = data.get("results", [])
                    elif isinstance(data, list):
                        results = data
                    else:
                        results = []

                    logger.info(
                        "ec3_materials_retrieved",
                        count=len(results),
                    )
                    return results
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
