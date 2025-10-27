# EPD Verification Fields - Complete Enumeration

## Overview

MOTHRA imports **40+ verification fields** from EC3 EPD data, organized into 15 categories for carbon verification professionals (TÜV, DNV, SGS, etc.).

All fields are stored in the `carbon_entity_verification` table with additional structured metadata in the `verification_metadata` JSONB column.

---

## Field Categories

### 1. GHG Emissions & Carbon Metrics (Primary)

**Direct Database Fields:**

| Field | Type | Description | Example | Standard |
|-------|------|-------------|---------|----------|
| `gwp_total` | float | Total Global Warming Potential | 250.5 kg CO2e | ISO 14067 |
| `gwp_co2` | float | CO2 component of GWP | 220.3 kg CO2 | ISO 14067 |
| `gwp_ch4` | float | CH4 component (CO2e) | 25.2 kg CO2e | ISO 14067 |
| `gwp_n2o` | float | N2O component (CO2e) | 5.0 kg CO2e | ISO 14067 |
| `gwp_biogenic` | float | Biogenic carbon (separate per EN 15804) | -15.3 kg CO2 | EN 15804 |
| `gwp_fossil` | float | Fossil carbon only | 265.8 kg CO2 | EN 15804 |
| `gwp_luluc` | float | Land use/land use change | 2.1 kg CO2e | ISO 14067 |

**Why Verifiers Need This:**
- Distinguish biogenic vs fossil carbon per EN 15804 requirements
- Verify GWP calculation methodology (100-year horizon)
- Check gas-specific contributions for accuracy
- Validate LULUC accounting for agriculture/forestry products

---

### 2. LCA Stages (EN 15804 Lifecycle Assessment)

**Direct Database Fields:**

| Field | Type | Description | Example | Standard |
|-------|------|-------------|---------|----------|
| `lca_stages_included` | list[str] | Which stages are included | ["A1", "A2", "A3", "C3", "C4", "D"] | EN 15804 |
| `lca_stage_emissions` | dict | Emissions by stage (kg CO2e) | {"A1": 120.5, "A2": 15.2, "A3": 85.3, "D": -10.5} | EN 15804 |

**LCA Stage Definitions (EN 15804+A2:2019):**

**Product Stage (A1-A3):**
- **A1**: Raw material supply (extraction, processing)
- **A2**: Transport to manufacturer
- **A3**: Manufacturing

**Construction Process Stage (A4-A5):**
- **A4**: Transport to building site
- **A5**: Installation/construction

**Use Stage (B1-B7):**
- **B1**: Use (direct emissions during use)
- **B2**: Maintenance
- **B3**: Repair
- **B4**: Replacement
- **B5**: Refurbishment
- **B6**: Operational energy use
- **B7**: Operational water use

**End-of-Life Stage (C1-C4):**
- **C1**: Deconstruction/demolition
- **C2**: Transport to waste processing
- **C3**: Waste processing (recycling, incineration)
- **C4**: Disposal (landfill)

**Benefits Beyond Life Cycle (Module D):**
- **D**: Reuse, recovery, recycling potential (negative emissions credited)

**Why Verifiers Need This:**
- Verify "cradle-to-gate" (A1-A3) vs "cradle-to-grave" (A1-C4) scope
- Check Module D accounting for circular economy benefits
- Ensure stage-specific data quality meets PCR requirements
- Validate omitted stages are justified

---

### 3. Additional Environmental Indicators (Beyond Carbon)

**Stored in `verification_metadata.environmental_indicators`:**

| Indicator | Unit | Description | Standard |
|-----------|------|-------------|----------|
| `acidification_potential` | kg SO2e | Acidification of soil and water | EN 15804 |
| `eutrophication_potential` | kg PO4e | Nutrient enrichment (algae blooms) | EN 15804 |
| `ozone_depletion_potential` | kg CFC-11e | Stratospheric ozone depletion | EN 15804 |
| `smog_formation_potential` | kg O3e | Photochemical ozone creation (POCP) | EN 15804 |
| `abiotic_depletion_elements` | kg Sbe | Mineral/metal resource depletion | EN 15804 |
| `abiotic_depletion_fossil` | MJ | Fossil fuel resource depletion | EN 15804 |
| `water_use` | m³ | Net freshwater consumption | EN 15804 |
| `land_use` | m²a | Land occupation/transformation | EN 15804 |
| `primary_energy_renewable` | MJ | Renewable energy demand | EN 15804 |
| `primary_energy_nonrenewable` | MJ | Non-renewable energy demand | EN 15804 |

**Why Verifiers Need This:**
- EN 15804 mandates reporting 15+ environmental indicators
- Green building certifications (LEED, BREEAM) require multiple indicators
- Avoid "carbon tunnel vision" - materials may be low-carbon but high water use
- Trade-off analysis for material selection decisions

---

### 4. Material Composition

**Stored in `verification_metadata.material_composition`:**

| Field | Type | Description | Example | Certification |
|-------|------|-------------|---------|---------------|
| `recycled_content_percent` | float | Total recycled content | 35.0 | ISO 14021 |
| `post_consumer_percent` | float | Post-consumer recycled | 20.0 | ISO 14021 |
| `pre_consumer_percent` | float | Pre-consumer recycled (industrial scrap) | 15.0 | ISO 14021 |
| `renewable_content_percent` | float | Bio-based/renewable materials | 60.0 | ISO 16128 |
| `rapidly_renewable_percent` | float | 10-year growth cycle materials | 45.0 | LEED |

**Why Verifiers Need This:**
- Verify recycled content claims per ISO 14021 requirements
- LEED MR credits require documentation
- Differentiate post-consumer (higher value) from pre-consumer
- Validate bio-based content for biogenic carbon claims
- Check consistency with GWP biogenic values

---

### 5. Manufacturing & Plant Details

**Stored in `verification_metadata.manufacturing`:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `plant_name` | string | Manufacturing facility name | "Portland Cement Plant 3" |
| `plant_location` | string | Plant address/city | "Seattle, WA" |
| `plant_country` | string | Country code | "US" |
| `manufacturing_process` | string | Production technology | "Dry kiln process with preheater" |

**Why Verifiers Need This:**
- Site-specific EPDs require plant identification
- Verify geographic representativeness
- Check if declared plant matches manufacturer claims
- Validate transport distance assumptions (A2, A4 stages)

---

### 6. Declared Units & Functional Units

**Direct Database Fields:**

| Field | Type | Description | Example | Standard |
|-------|------|-------------|---------|----------|
| `declared_unit` | string | Unit for EPD values | "1 m³" | EN 15804 |
| `functional_unit` | string | Performance-based unit | "1 m² wall, R-19, 50 years" | ISO 21930 |
| `reference_service_life` | int | Expected lifespan (years) | 50 | ISO 15686 |

**Stored in `verification_metadata.raw_epd_summary`:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `mass_per_unit` | float | Mass per declared unit (kg) | 2400.0 |

**Why Verifiers Need This:**
- Compare products fairly using functional equivalence
- Normalize to different units for comparisons
- Verify service life assumptions for B-stage calculations
- Check if declared unit matches PCR requirements

---

### 7. EPD Registration & Metadata

**Direct Database Fields:**

| Field | Type | Description | Example | Purpose |
|-------|------|-------------|---------|---------|
| `epd_registration_number` | string | Unique EPD identifier | "EPD-BRE-00234567" | Traceability |
| `epd_version` | string | Version number | "2.1" | Track updates |
| `epd_program_operator` | string | EPD program | "IBU (Institut Bauen und Umwelt)" | Authority |
| `openepd_id` | string | OpenEPD UUID | "ec3abcd1234..." | Digital ID |
| `ec3_material_id` | string | EC3 material ID | "12345" | Database key |

**Why Verifiers Need This:**
- Lookup original EPD document for verification
- Check if EPD is current or superseded
- Validate program operator is accredited (ISO 14025)
- Cross-reference with program operator databases

---

### 8. Temporal Validity (Critical!)

**Direct Database Fields:**

| Field | Type | Description | Example | Requirement |
|-------|------|-------------|---------|-------------|
| `published_date` | datetime | EPD publication date | 2022-03-15 | ISO 14025 |
| `valid_from_date` | datetime | Start of validity period | 2022-04-01 | ISO 14025 |
| `expiry_date` | datetime | EPD expiration date | 2027-03-31 | ISO 14025 |

**Stored in `verification_metadata.data_quality`:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `temporal_coverage` | string | Data collection period | "2020-2021 (12 months)" |

**Why Verifiers Need This:**
- EPDs typically valid for 5 years (ISO 14025)
- Reject expired EPDs for procurement decisions
- Check data collection period for representativeness
- Verify publication delay is reasonable (<2 years)

---

### 9. Geographic Validity

**Stored in `verification_metadata.geographic_scope`:**

| Type | Example | Validity |
|------|---------|----------|
| Country-specific | ["US"] | Valid only in specified country |
| Regional | ["North America"] | Valid for region |
| Global | ["Global"] | Representative globally |
| Multi-country | ["US", "CA", "MX"] | USMCA region |

**Stored in `verification_metadata.data_quality`:**

| Field | Description | Example |
|-------|-------------|---------|
| `geographic_coverage` | Production locations covered | "3 plants in Pacific Northwest" |

**Why Verifiers Need This:**
- Check if EPD is valid for project location
- Verify geographic representativeness of LCA data
- Regional grids affect electricity emissions (A3, B6)
- Transport distances vary by geography (A2, A4)

---

### 10. PCR (Product Category Rules) Details

**Direct Database Fields:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `pcr_reference` | string | PCR identifier | "EN 15804+A2:2019/PCR-012" |
| `pcr_version` | string | PCR version | "3.1" |
| `pcr_publisher` | string | PCR program operator | "ECO Platform" |

**Why Verifiers Need This:**
- PCR defines product category-specific rules
- Verify EPD complies with correct PCR
- Check if PCR is superseded (affects comparability)
- EN 15804+A2 (2019) is current standard - A1 (2013) is outdated

---

### 11. Verification Body & Standards

**Direct Database Fields:**

| Field | Type | Description | Example | Standard |
|-------|------|-------------|---------|----------|
| `verification_status` | enum | Current status | "verified" | MOTHRA |
| `verification_body` | string | Third-party verifier | "TÜV SÜD" | ISO 14025 |
| `verification_date` | datetime | Verification completion | 2022-02-28 | ISO 14025 |
| `verification_standards` | list[str] | Standards met | ["EN_15804", "ISO_14067"] | ISO 14025 |
| `third_party_verified` | bool | Externally verified? | true | ISO 14025 |

**Why Verifiers Need This:**
- ISO 14025 requires independent third-party verification
- Check verifier is accredited (EN ISO/IEC 17029)
- Validation ≠ Verification (validation is less rigorous)
- Major verifiers: TÜV, DNV, SGS, Bureau Veritas, UL

---

### 12. Compliance Flags

**Direct Database Fields:**

| Field | Type | Description | Pass Criteria |
|-------|------|-------------|---------------|
| `iso_14067_compliant` | bool | Product Carbon Footprint standard | LCA per ISO 14044, report per 14067 |
| `en_15804_compliant` | bool | Construction EPD standard | Includes modules A1-A3 minimum, reports all 15+ indicators |
| `iso_21930_compliant` | bool | Core rules for construction EPDs | Functional unit, 50+ year service life, building-level |

**Why Verifiers Need This:**
- Quick screening for standard compliance
- EN 15804 required for EU construction products
- ISO 14067 required for Carbon Border Adjustment Mechanism (CBAM)
- ISO 21930 adds building-specific requirements

---

### 13. Data Quality Indicators (ISO 14044)

**Stored in `verification_metadata.data_quality`:**

| Indicator | Description | Example | Quality Check |
|-----------|-------------|---------|---------------|
| `temporal_coverage` | Time period of data | "2020-2021 (12 months)" | ≥12 months preferred |
| `geographic_coverage` | Production locations | "5 plants in EU" | Matches declared geography |
| `technological_coverage` | Process representativeness | "Average of 12 cement plants" | Weighted by production volume |
| `data_quality_rating` | Overall quality score | "Good (3.5/5)" | Per pedigree matrix |

**ISO 14044 Data Quality Dimensions:**
1. **Temporal**: How recent is the data?
2. **Geographic**: Does it match product geography?
3. **Technological**: Representative of actual production?
4. **Precision**: Measurement accuracy
5. **Completeness**: Coverage of processes

**Why Verifiers Need This:**
- Assess reliability of LCA results
- Higher quality data = more credible EPD
- Check if proxy data was used (lower quality)
- Verify data quality meets PCR requirements

---

### 14. LCA Methodology Details

**Stored in `verification_metadata.lca_methodology`:**

| Field | Description | Example | Purpose |
|-------|-------------|---------|---------|
| `lca_software` | LCA modeling tool | "GaBi 10.5" | Reproducibility |
| `database_version` | Background data | "ecoinvent 3.8" | Data quality |
| `cutoff_rules` | Exclusion threshold | "1% mass/energy" | Completeness |
| `allocation_method` | Multi-output allocation | "Economic allocation" | ISO 14044 |

**Common LCA Databases:**
- **ecoinvent**: Most comprehensive (18,000+ processes)
- **GaBi**: Industry-focused
- **US LCI**: Free, US-specific
- **ELCD**: EU official database

**Allocation Methods (ISO 14044):**
- **Physical**: By mass, energy, or other physical property
- **Economic**: By market value
- **System expansion**: Avoided burden approach

**Why Verifiers Need This:**
- Verify methodology meets ISO 14044 requirements
- Check database version is current (<5 years old)
- Validate allocation method is appropriate for product
- Assess reproducibility of study

---

### 15. Scenarios & Assumptions

**Stored in `verification_metadata.scenarios`:**

| Scenario | Description | Example | Impact |
|----------|-------------|---------|--------|
| `transport_distance_km` | Average transport to site | 500 km | Affects A2, A4 |
| `transport_mode` | Vehicle type | "Diesel truck 20-26t" | Emission factor |
| `installation_scenario` | Construction method | "Wet mortar application" | A5 stage |
| `end_of_life_scenario` | Disposal method | "75% recycling, 25% landfill" | C3, C4, D |

**Why Verifiers Need This:**
- Scenarios significantly affect results (esp. transport, EOL)
- Check if assumptions are conservative or optimistic
- Verify scenarios match PCR default scenarios
- Assess sensitivity to assumption changes

---

### 16. Product Specifications (Technical Performance)

**Stored in `verification_metadata.product_specifications`:**

| Property | Unit | Example | Purpose |
|----------|------|---------|---------|
| `density` | kg/m³ | 2400 | Mass calculations |
| `thickness` | mm | 200 | Coverage calculations |
| `compressive_strength` | MPa | 30 | Structural performance |
| `thermal_conductivity` | W/(m·K) | 0.035 | Insulation performance |

**Why Verifiers Need This:**
- Verify functional unit makes sense for product
- Check if performance meets application requirements
- Compare products on equal performance basis
- Validate technical specs match EPD document

---

## Database Schema

### Primary Fields (carbon_entity_verification table)

```sql
CREATE TABLE carbon_entity_verification (
    id UUID PRIMARY KEY,
    entity_id UUID NOT NULL,  -- FK to carbon_entities

    -- GHG & Carbon
    gwp_total FLOAT,
    gwp_co2 FLOAT,
    gwp_ch4 FLOAT,
    gwp_n2o FLOAT,
    gwp_biogenic FLOAT,
    gwp_fossil FLOAT,
    gwp_luluc FLOAT,

    -- LCA Stages
    lca_stages_included TEXT[],
    lca_stage_emissions JSONB,

    -- Units
    declared_unit VARCHAR(255),
    functional_unit TEXT,
    reference_service_life INTEGER,

    -- EPD Registration
    epd_registration_number VARCHAR(255),
    epd_version VARCHAR(50),
    epd_program_operator VARCHAR(255),
    openepd_id VARCHAR(255),
    ec3_material_id VARCHAR(255),

    -- PCR
    pcr_reference VARCHAR(500),
    pcr_version VARCHAR(50),
    pcr_publisher VARCHAR(255),

    -- Temporal Validity
    published_date TIMESTAMPTZ,
    valid_from_date TIMESTAMPTZ,
    expiry_date TIMESTAMPTZ,

    -- Verification
    verification_status VARCHAR(50),
    verification_standards TEXT[],
    verification_body VARCHAR(255),
    verification_date TIMESTAMPTZ,
    third_party_verified BOOLEAN,

    -- Compliance
    iso_14067_compliant BOOLEAN,
    en_15804_compliant BOOLEAN,
    iso_21930_compliant BOOLEAN,

    -- Document
    document_url TEXT,

    -- Extended metadata (JSONB for flexibility)
    verification_metadata JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Metadata Structure (verification_metadata JSONB)

```json
{
  "source": "EC3/Building Transparency",
  "import_date": "2025-10-27T12:00:00Z",

  "environmental_indicators": {
    "acidification_potential": 0.45,
    "eutrophication_potential": 0.12,
    "ozone_depletion_potential": 0.000002,
    "smog_formation_potential": 15.3,
    "abiotic_depletion_elements": 0.0001,
    "abiotic_depletion_fossil": 2500,
    "water_use": 0.85,
    "land_use": 0.05,
    "primary_energy_renewable": 150,
    "primary_energy_nonrenewable": 2800
  },

  "material_composition": {
    "recycled_content_percent": 35.0,
    "post_consumer_percent": 20.0,
    "pre_consumer_percent": 15.0,
    "renewable_content_percent": 5.0
  },

  "manufacturing": {
    "plant_name": "Cement Plant 3",
    "plant_location": "Seattle, WA",
    "plant_country": "US",
    "manufacturing_process": "Dry kiln with preheater"
  },

  "geographic_scope": ["US", "Canada"],

  "data_quality": {
    "temporal_coverage": "2020-2021 (12 months)",
    "geographic_coverage": "5 plants in North America",
    "technological_coverage": "Weighted average by production volume",
    "data_quality_rating": "Good (3.5/5)"
  },

  "lca_methodology": {
    "lca_software": "GaBi 10.5",
    "database_version": "ecoinvent 3.8",
    "cutoff_rules": "1% mass/energy/environmental relevance",
    "allocation_method": "Economic allocation"
  },

  "scenarios": {
    "transport_distance_km": 500,
    "transport_mode": "Diesel truck 20-26t",
    "installation_scenario": "Standard installation",
    "end_of_life_scenario": "75% recycling, 25% landfill"
  },

  "product_specifications": {
    "density": 2400,
    "thickness": 200,
    "compressive_strength": 30,
    "thermal_conductivity": 0.035
  },

  "raw_epd_summary": {
    "name": "Portland Cement CEM I 42.5",
    "manufacturer": "ABC Cement Company",
    "category": "Concrete",
    "mass_per_unit": 2400
  }
}
```

---

## Query Examples for Verifiers

### 1. Find Low-Carbon Materials with High Recycled Content

```sql
SELECT
    e.name,
    v.gwp_total,
    v.verification_metadata->'material_composition'->>'recycled_content_percent' as recycled_content,
    v.epd_registration_number
FROM carbon_entities e
JOIN carbon_entity_verification v ON e.id = v.entity_id
WHERE
    e.category_hierarchy @> ARRAY['concrete']
    AND v.gwp_total < 300
    AND (v.verification_metadata->'material_composition'->>'recycled_content_percent')::float > 20
    AND v.third_party_verified = true
    AND v.expiry_date > NOW()
ORDER BY v.gwp_total ASC
LIMIT 20;
```

### 2. EPDs by LCA Stage Completeness

```sql
SELECT
    v.lca_stages_included,
    COUNT(*) as epd_count,
    AVG(v.gwp_total) as avg_gwp
FROM carbon_entity_verification v
WHERE
    v.en_15804_compliant = true
    AND v.expiry_date > NOW()
GROUP BY v.lca_stages_included
ORDER BY epd_count DESC;
```

### 3. Environmental Trade-offs Analysis

```sql
SELECT
    e.name,
    v.gwp_total as carbon,
    (v.verification_metadata->'environmental_indicators'->>'water_use')::float as water,
    (v.verification_metadata->'environmental_indicators'->>'acidification_potential')::float as acidification
FROM carbon_entities e
JOIN carbon_entity_verification v ON e.id = v.entity_id
WHERE
    e.category_hierarchy @> ARRAY['insulation']
    AND v.gwp_total IS NOT NULL
ORDER BY v.gwp_total ASC;
```

### 4. Expiring EPDs (Needs Update)

```sql
SELECT
    e.name,
    v.epd_registration_number,
    v.published_date,
    v.expiry_date,
    v.expiry_date - NOW() as days_until_expiry
FROM carbon_entities e
JOIN carbon_entity_verification v ON e.id = v.entity_id
WHERE
    v.expiry_date BETWEEN NOW() AND NOW() + INTERVAL '6 months'
ORDER BY v.expiry_date ASC;
```

### 5. Verification Body Statistics

```sql
SELECT
    v.verification_body,
    COUNT(*) as epds_verified,
    AVG(v.gwp_total) as avg_gwp,
    COUNT(*) FILTER (WHERE v.iso_14067_compliant) as iso_14067_count,
    COUNT(*) FILTER (WHERE v.en_15804_compliant) as en_15804_count
FROM carbon_entity_verification v
WHERE v.verification_body IS NOT NULL
GROUP BY v.verification_body
ORDER BY epds_verified DESC;
```

---

## Standards Reference

### ISO Standards

| Standard | Title | Relevance |
|----------|-------|-----------|
| **ISO 14025** | Environmental labels and declarations - Type III | EPD program requirements |
| **ISO 14040** | Environmental management - LCA - Principles | LCA framework |
| **ISO 14044** | Environmental management - LCA - Requirements | LCA methodology |
| **ISO 14067** | Greenhouse gases - Carbon footprint of products | Product carbon footprint |
| **ISO 14064-1** | GHG inventories - Organization level | Corporate emissions |
| **ISO 21930** | Sustainability in buildings - Environmental product declarations | Construction EPDs |
| **ISO 15686** | Buildings - Service life planning | Reference service life |

### EN Standards (European Norms)

| Standard | Title | Relevance |
|----------|-------|-----------|
| **EN 15804+A2** | EPDs for construction products | EU construction EPD rules |
| **EN ISO/IEC 17029** | Conformity assessment - Verification bodies | Verifier accreditation |

### Other Standards

| Standard | Title | Relevance |
|----------|-------|-----------|
| **GHG Protocol** | Product Life Cycle Standard | Corporate carbon accounting |
| **PAS 2050** | Specification for carbon footprinting | UK product footprints |

---

## Field Availability by EPD Program

Not all EPD programs require all fields. Here's what to expect:

| Program | EPD Count | Fields Typically Included | Missing Fields |
|---------|-----------|---------------------------|----------------|
| **IBU (Germany)** | 2,000+ | All EN 15804 fields, high data quality | Sometimes missing Module D |
| **EPD International** | 1,500+ | Complete per ISO 21930 | Varies by manufacturer |
| **UL Environment** | 1,000+ | Strong on material composition | Less detailed scenarios |
| **NSF International** | 800+ | Good PCR compliance | Limited LCA methodology details |
| **BRE (UK)** | 600+ | Excellent on UK data | Less global coverage |

---

## API Response Field Mapping

How EC3 API fields map to MOTHRA database:

```python
# EC3 API Response → MOTHRA Field
{
    "gwp": { "total": 250.5 }  →  gwp_total = 250.5
    "gwp_biogenic": -15.3      →  gwp_biogenic = -15.3
    "lca_stages": {
        "a1": 120.5,
        "a2": 15.2,
        "a3": 85.3
    }                           →  lca_stages_included = ["A1", "A2", "A3"]
                                →  lca_stage_emissions = {"A1": 120.5, "A2": 15.2, "A3": 85.3}

    "declared_unit": "1 m³"    →  declared_unit = "1 m³"
    "epd_number": "EPD-123"    →  epd_registration_number = "EPD-123"
    "verifier": "TÜV SÜD"      →  verification_body = "TÜV SÜD"

    "recycled_content": 35     →  verification_metadata.material_composition.recycled_content_percent = 35.0
    "ap": 0.45                 →  verification_metadata.environmental_indicators.acidification_potential = 0.45
    "plant": {
        "name": "Plant 3",
        "location": "Seattle, WA"
    }                          →  verification_metadata.manufacturing.plant_name = "Plant 3"
                               →  verification_metadata.manufacturing.plant_location = "Seattle, WA"
}
```

---

## Summary Statistics

After bulk import, you'll have:

| Category | Fields | Storage |
|----------|--------|---------|
| **Direct DB columns** | 30 fields | Indexed for fast queries |
| **Environmental indicators** | 10+ metrics | JSONB metadata |
| **Material composition** | 5 fields | JSONB metadata |
| **Manufacturing details** | 4 fields | JSONB metadata |
| **Data quality indicators** | 4 metrics | JSONB metadata |
| **LCA methodology** | 4 fields | JSONB metadata |
| **Scenarios** | 4 assumptions | JSONB metadata |
| **Product specs** | 4+ properties | JSONB metadata |
| **Total** | **65+ fields** | Comprehensive verification data |

---

## Next Steps for Verifiers

1. **Import EPDs**: Run `python scripts/bulk_import_epds.py` to populate database
2. **Query Data**: Use SQL examples above to analyze verification data
3. **Export Reports**: Generate CSV reports for certification submissions
4. **Build Workflows**: Create custom queries for specific standards (LEED, BREEAM, etc.)
5. **API Integration**: Connect to external tools via MOTHRA API

---

## Support & Documentation

- **MOTHRA Docs**: See `README.md` for system architecture
- **EC3 API Docs**: https://docs.buildingtransparency.org/
- **EN 15804 Standard**: Purchase from ISO or national standards bodies
- **ISO 14067 Guidance**: https://www.iso.org/standard/71206.html

---

**Last Updated**: 2025-10-27
**Version**: 1.0
**Author**: MOTHRA Development Team
