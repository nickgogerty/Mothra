"""
Professional Carbon Verification Models.

Comprehensive data models for carbon verification meeting TUV, DNV, SGS standards.
Supports:
- ISO 14067:2018 (Product Carbon Footprint)
- ISO 14064-1/2/3 (GHG Verification)
- GHG Protocol (Scope 1, 2, 3)
- EN 15804+A2 (EPD LCA stages A1-D)
- EPD requirements and PCR compliance
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, DATERANGE, UUID
from sqlalchemy.orm import Mapped, mapped_column

from mothra.db.base import Base


class GHGScope(str, Enum):
    """GHG Protocol Scopes."""

    SCOPE_1 = "scope_1"  # Direct emissions
    SCOPE_2 = "scope_2"  # Indirect (purchased energy)
    SCOPE_3 = "scope_3"  # Value chain emissions
    BIOGENIC = "biogenic"  # Biogenic carbon


class LCAStage(str, Enum):
    """EN 15804 LCA Stages."""

    # Product Stage (A1-A3)
    A1_RAW_MATERIAL = "A1"  # Raw material supply
    A2_TRANSPORT = "A2"  # Transport to manufacturer
    A3_MANUFACTURING = "A3"  # Manufacturing

    # Construction Stage (A4-A5)
    A4_TRANSPORT_TO_SITE = "A4"  # Transport to building site
    A5_INSTALLATION = "A5"  # Installation/construction

    # Use Stage (B1-B7)
    B1_USE = "B1"  # Use or application
    B2_MAINTENANCE = "B2"  # Maintenance
    B3_REPAIR = "B3"  # Repair
    B4_REPLACEMENT = "B4"  # Replacement
    B5_REFURBISHMENT = "B5"  # Refurbishment
    B6_OPERATIONAL_ENERGY = "B6"  # Operational energy
    B7_OPERATIONAL_WATER = "B7"  # Operational water

    # End of Life Stage (C1-C4)
    C1_DECONSTRUCTION = "C1"  # Deconstruction/demolition
    C2_TRANSPORT_TO_WASTE = "C2"  # Transport to waste processing
    C3_WASTE_PROCESSING = "C3"  # Waste processing (reuse/recycling)
    C4_DISPOSAL = "C4"  # Final disposal

    # Beyond Building Life Cycle
    D_BENEFITS_LOADS = "D"  # Reuse, recovery, recycling potential


class VerificationStandard(str, Enum):
    """Verification standards."""

    ISO_14067 = "ISO 14067:2018"  # Product carbon footprint
    ISO_14064_1 = "ISO 14064-1"  # Organizational GHG inventories
    ISO_14064_2 = "ISO 14064-2"  # Project-level GHG quantification
    ISO_14064_3 = "ISO 14064-3"  # GHG verification
    GHG_PROTOCOL_CORPORATE = "GHG Protocol Corporate"
    GHG_PROTOCOL_PRODUCT = "GHG Protocol Product"
    PAS_2050 = "PAS 2050"  # Specification for carbon footprint
    EN_15804 = "EN 15804+A2"  # EPDs for construction products
    ISO_21930 = "ISO 21930"  # Core rules for construction EPDs


class VerificationStatus(str, Enum):
    """Verification status."""

    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class EPDProgramOperator(str, Enum):
    """Known EPD Program Operators."""

    INTERNATIONAL_EPD = "International EPD System"
    IBU = "IBU (Institut Bauen und Umwelt)"
    EPD_NORWAY = "EPD Norge"
    AUSTRALASIAN_EPD = "Australasian EPD Programme"
    FDES_INIES = "FDES INIES"
    UL_ENVIRONMENT = "UL Environment"
    BUILDING_TRANSPARENCY = "Building Transparency (EC3)"
    OTHER = "Other"


class CarbonEntityVerification(Base):
    """
    Professional carbon verification data.

    Tracks comprehensive verification information for carbon entities
    meeting TUV, DNV, SGS, and other third-party verification requirements.
    """

    __tablename__ = "carbon_entity_verification"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Link to main entity
    entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carbon_entities.id", ondelete="CASCADE"),
        index=True,
    )

    # === GHG Protocol & ISO 14064 ===

    # Scope classification (can have multiple scopes)
    ghg_scopes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Detailed scope 3 categories (if applicable)
    # Per GHG Protocol: 15 categories (purchased goods, capital goods, etc.)
    scope_3_categories: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=True)

    # === LCA Stages (EN 15804 for EPDs) ===

    # Which LCA stages are included in this data
    lca_stages_included: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list
    )

    # Emissions by LCA stage (kg CO2e per stage)
    lca_stage_emissions: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # Example: {"A1": 12.5, "A2": 3.2, "A3": 8.7, "D": -2.1}

    # === EPD Specific Fields ===

    # EPD registration number (if applicable)
    epd_registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # EPD program operator
    epd_program_operator: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Product Category Rules (PCR) reference
    pcr_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Declared unit (e.g., "1 kg", "1 m²", "1 m³")
    declared_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Functional/reference unit for comparison
    functional_unit: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Reference service life (years)
    reference_service_life: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # === Emission Values ===

    # Global Warming Potential (GWP) - Total
    gwp_total: Mapped[float | None] = mapped_column(Float, nullable=True)

    # GWP by gas type
    gwp_co2: Mapped[float | None] = mapped_column(Float, nullable=True)
    gwp_ch4: Mapped[float | None] = mapped_column(Float, nullable=True)
    gwp_n2o: Mapped[float | None] = mapped_column(Float, nullable=True)
    gwp_hfcs: Mapped[float | None] = mapped_column(Float, nullable=True)
    gwp_pfcs: Mapped[float | None] = mapped_column(Float, nullable=True)
    gwp_sf6: Mapped[float | None] = mapped_column(Float, nullable=True)
    gwp_nf3: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Biogenic carbon (separately reported per EN 15804)
    gwp_biogenic: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Land use change emissions
    gwp_luluc: Mapped[float | None] = mapped_column(Float, nullable=True)

    # === Other Environmental Indicators (EN 15804) ===

    # Additional impact categories
    environmental_indicators: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # Can include: ODP, AP, EP, POCP, ADP (elements), ADP (fossil), WDP, etc.

    # === Verification Information ===

    # Verification status
    verification_status: Mapped[str] = mapped_column(
        String(20), default=VerificationStatus.PENDING.value
    )

    # Verification standards applied
    verification_standards: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list
    )

    # Verification body (TUV, DNV, SGS, etc.)
    verification_body: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Verifier name/organization
    verifier_name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Verification date
    verification_date: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    # Expiry date
    expiry_date: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)

    # Verification certificate number
    certificate_number: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # === Uncertainty and Data Quality ===

    # Uncertainty range (+/- %)
    uncertainty_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Data quality rating (1-5, 5 = highest)
    data_quality_rating: Mapped[int | None] = mapped_column(
        Integer,
        CheckConstraint("data_quality_rating >= 1 AND data_quality_rating <= 5"),
        nullable=True,
    )

    # Data quality indicators per ISO 14044
    data_quality_indicators: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    # Can include: temporal_coverage, geographical_coverage, technology_coverage,
    # precision, completeness, representativeness, consistency, reproducibility

    # === System Boundaries ===

    # System boundary description
    system_boundary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cutoff criteria (% of mass/energy/environmental impact)
    cutoff_criteria: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Allocation method (if applicable)
    allocation_method: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # === Temporal Coverage ===

    # Reference year for data
    reference_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Data collection period
    data_collection_period: Mapped[str | None] = mapped_column(DATERANGE, nullable=True)

    # === Geographic Validity ===

    # Countries/regions where data is valid
    geographic_validity: Mapped[list[str]] = mapped_column(
        ARRAY(String), default=list
    )

    # === Technology Coverage ===

    # Technology type/mix
    technology_type: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Representative technology or mix
    representative_technology: Mapped[str | None] = mapped_column(Text, nullable=True)

    # === Product Classification ===

    # UNSPSC code (United Nations Standard Products and Services Code)
    unspsc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # CAS number (if chemical)
    cas_number: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # CPC code (Central Product Classification)
    cpc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # === EC3 Integration ===

    # EC3 material ID (if from EC3/Building Transparency)
    ec3_material_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # OpenEPD ID
    openepd_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # === Compliance Flags ===

    # ISO 14067 compliant
    iso_14067_compliant: Mapped[bool] = mapped_column(default=False)

    # EN 15804 compliant
    en_15804_compliant: Mapped[bool] = mapped_column(default=False)

    # GHG Protocol compliant
    ghg_protocol_compliant: Mapped[bool] = mapped_column(default=False)

    # Third-party verified
    third_party_verified: Mapped[bool] = mapped_column(default=False)

    # === Additional Metadata ===

    # Comments/notes from verifier
    verifier_comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Link to verification report/EPD document
    document_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Additional verification metadata
    verification_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # === Timestamps ===

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # === Indexes ===

    __table_args__ = (
        Index("idx_verification_entity", "entity_id"),
        Index("idx_verification_status", "verification_status"),
        Index("idx_verification_epd_number", "epd_registration_number"),
        Index("idx_verification_ec3_id", "ec3_material_id"),
        Index("idx_verification_openepd_id", "openepd_id"),
        Index("idx_verification_body", "verification_body"),
        Index("idx_verification_date", "verification_date"),
    )


class Scope3Category(Base):
    """
    GHG Protocol Scope 3 Categories.

    The 15 categories of Scope 3 emissions per GHG Protocol.
    """

    __tablename__ = "scope3_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Link to verification record
    verification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carbon_entity_verification.id", ondelete="CASCADE"),
        index=True,
    )

    # Category number (1-15)
    category_number: Mapped[int] = mapped_column(
        Integer,
        CheckConstraint("category_number >= 1 AND category_number <= 15"),
    )

    # Category name
    category_name: Mapped[str] = mapped_column(String(200))

    # Emissions for this category (kg CO2e)
    emissions_kg_co2e: Mapped[float] = mapped_column(Float)

    # Percentage of total scope 3
    percentage_of_scope3: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Calculation methodology
    calculation_method: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Data sources
    data_sources: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Data quality
    data_quality: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Additional data (renamed from metadata to avoid SQLAlchemy reserved word)
    additional_data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), nullable=False
    )


# Scope 3 category reference data
SCOPE_3_CATEGORIES = {
    1: "Purchased goods and services",
    2: "Capital goods",
    3: "Fuel and energy related activities",
    4: "Upstream transportation and distribution",
    5: "Waste generated in operations",
    6: "Business travel",
    7: "Employee commuting",
    8: "Upstream leased assets",
    9: "Downstream transportation and distribution",
    10: "Processing of sold products",
    11: "Use of sold products",
    12: "End-of-life treatment of sold products",
    13: "Downstream leased assets",
    14: "Franchises",
    15: "Investments",
}
