# Government Emissions Data Sources

This document catalogs the top 10 government and international emissions data sources integrated into Mothra's carbon database.

Last Updated: 2025-10-28

## Overview

Mothra ingests emissions-related factors and facility data from authoritative government sources worldwide. These sources provide the foundation for accurate carbon accounting and lifecycle assessments.

## Top 10 Data Sources

### 1. UK DEFRA 2025 GHG Conversion Factors ⭐ CRITICAL

**Source:** UK Department for Energy Security and Net Zero (DESNZ), formerly DEFRA
**URL:** https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2025
**Collection:** https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting

**Data Type:** Emission Factors
**Format:** Excel (XLSX)
**Geographic Scope:** UK, International
**Update Frequency:** Annual (published June each year)

**Content:**
- Comprehensive GHG conversion factors for corporate reporting
- Covers fuels, electricity, transport (road, rail, air, sea), refrigerants, water, waste, materials
- Both condensed and full datasets available
- Includes CO2, CH4, N2O, and CO2e values
- Scope 1, 2, and 3 emission factors

**2025 Updates:**
- Aviation emissions reduced 16-42% across all flight categories
- Battery EV emissions down 16%
- UK electricity emissions down 14.5%

**Parser:** `uk_defra_parser.py`

---

### 2. EPA Supply Chain GHG Emission Factors v1.3 NAICS ⭐ CRITICAL

**Source:** US Environmental Protection Agency
**URL:** https://catalog.data.gov/dataset/supply-chain-greenhouse-gas-emission-factors-v1-3-by-naics-6
**Direct Download:** https://pasteur.epa.gov/uploads/10.23719/1531143/SupplyChainGHGEmissionFactors_v1.3.0_NAICS_byGHG_USD2022.csv
**GitHub:** https://github.com/USEPA/supply-chain-factors

**Data Type:** Emission Factors (Supply Chain Scope 3)
**Format:** CSV
**Geographic Scope:** USA
**Update Frequency:** Periodic (v1.3 released July 2024)

**Content:**
- 1,016 US commodity emission factors
- Organized by NAICS-6 (North American Industry Classification System)
- Based on 2022 GHG data
- Factors in kg CO2e per 2022 USD
- Three factor types:
  - Supply Chain Emissions without Margins (SEF)
  - Margins of Supply Chain Emissions (MEF)
  - Supply Chain Emissions with Margins (SEF+MEF)
- Individual GHG breakdowns: CO2, CH4, N2O, HFC, PFC, SF6, NF3

**Use Case:** Scope 3 greenhouse gas reporting for purchased goods and services

**Parser:** Custom CSV parser + `epa_ghgrp_parser.py` for facility data

---

### 3. EPA GHGRP Facility Emissions ⭐ CRITICAL

**Source:** US Environmental Protection Agency - Greenhouse Gas Reporting Program
**URL:** https://www.epa.gov/ghgreporting/data-sets
**API:** https://enviro.epa.gov/enviro/efservice/

**Data Type:** Facility-level Emissions
**Format:** Excel (XLSX), CSV, API
**Geographic Scope:** USA
**Update Frequency:** Annual

**Content:**
- 16,000+ facility emissions reports
- Industry types: Power plants, refineries, petroleum & natural gas, chemicals, waste, metals, etc.
- Facility details: Name, ID, location (lat/lon), city, state, ZIP
- Annual emissions by GHG type
- Comprehensive metadata

**Parser:** `epa_ghgrp_parser.py`

---

### 4. EPA GHG Emission Factors Hub 2025 ⭐ HIGH

**Source:** US Environmental Protection Agency
**URL:** https://www.epa.gov/climateleadership/ghg-emission-factors-hub
**Direct Download:** https://www.epa.gov/system/files/documents/2025-01/ghg-emission-factors-hub-2025.pdf

**Data Type:** Emission Factors
**Format:** PDF, Excel
**Geographic Scope:** USA
**Update Frequency:** Annual (January updates)

**Content:**
- Regularly updated emission factors for organizational GHG reporting
- Sources include:
  - EPA's Greenhouse Gas Reporting Program (GHGRP)
  - eGRID (electricity)
  - Inventory of U.S. GHG Emissions and Sinks
  - WARM (waste)
  - IPCC Fifth Assessment Report
- Covers electricity, mobile combustion, transportation, business travel

**2025 Update:** January 2025

---

### 5. EU ETS Verified Emissions ⭐ CRITICAL

**Source:** European Environment Agency
**URL:** https://www.eea.europa.eu/data-and-maps/data/european-union-emissions-trading-scheme-17

**Data Type:** Facility-level Verified Emissions
**Format:** Excel (XLSX), XML
**Geographic Scope:** EU
**Update Frequency:** Annual

**Content:**
- 16,000+ EU ETS installation emissions
- Verified emissions data from EU's carbon trading system
- Installation details and location
- Annual emissions and allowances
- Industry sectors covered by ETS

**Parser:** `eu_ets_parser.py`

---

### 6. EEA Emission Factor Database ⭐ HIGH

**Source:** European Environment Agency
**URL:** https://www.eea.europa.eu/publications/emep-eea-guidebook-2019/emission-factors-database

**Data Type:** Emission Factors
**Format:** Excel (XLSX), CSV, Interactive Database
**Geographic Scope:** EU, OECD, Global
**Update Frequency:** Periodic (2019 Guidebook)

**Content:**
- EMEP/EEA Guidebook emission factors
- Organized by NFR (Nomenclature For Reporting) codes
- Covers all major emission source categories
- Includes abatement efficiencies
- Methodologies for national GHG inventories

---

### 7. IPCC Emission Factor Database ⭐ HIGH

**Source:** Intergovernmental Panel on Climate Change
**URL:** https://www.ipcc-nggip.iges.or.jp/EFDB
**API Access:** https://ghgprotocol.org/Third-Party-Databases/IPCC-Emissions-Factor-Database

**Data Type:** Emission Factors
**Format:** HTML Tables, Database Export
**Geographic Scope:** Global
**Update Frequency:** Periodic

**Content:**
- Authoritative emission factors for GHG inventories
- Based on IPCC Guidelines for National GHG Inventories
- Sectors covered:
  - Energy (combustion, mobile, fugitive)
  - Industrial processes (minerals, chemicals, metals)
  - Agriculture (enteric fermentation, manure, rice, soil)
  - Waste (landfills, wastewater, incineration)
  - LULUCF (forestry, cropland, grassland)
- Includes uncertainty estimates
- Free access

**Parser:** `ipcc_emission_factors_parser.py`

---

### 8. IEA Emissions Factors 2024 🔒 MEDIUM

**Source:** International Energy Agency
**URL:** https://www.iea.org/data-and-statistics/data-product/emissions-factors-2024
**Methodology:** https://iea.blob.core.windows.net/assets/884cd44a-3a59-4359-9bc4-d5c5fb3cc66c/IEA_Methodology_Emission_Factors.pdf

**Data Type:** Emission Factors
**Format:** Excel (XLSX)
**Geographic Scope:** Global (200+ countries)
**Update Frequency:** Annual, with quarterly subscription option

**Content:**
- CO2 emission factors from electricity and heat generation
- Covers 1990-2022 time series
- Both combined electricity/heat and electricity-only generation
- Country-level data
- Methodology documentation available

**Access:** Requires free IEA account for download
**Subscription:** Multi-user licenses available

---

### 9. UK DEFRA 2024 GHG Conversion Factors ⭐ HIGH

**Source:** UK Department for Energy Security and Net Zero
**URL:** https://www.gov.uk/government/publications/greenhouse-gas-reporting-conversion-factors-2024

**Data Type:** Emission Factors (Historical)
**Format:** Excel (XLSX)
**Geographic Scope:** UK, International
**Update Frequency:** Annual

**Content:**
- Historical 2024 conversion factors
- Same structure as 2025 edition
- Useful for time-series analysis and historical reporting
- Maintained for compliance with reporting periods

**Parser:** `uk_defra_parser.py`

---

### 10. Climatiq BEIS Data (API) 🌐 MEDIUM

**Source:** Climatiq (third-party aggregator of UK government data)
**URL:** https://www.climatiq.io/data/source/beis

**Data Type:** Emission Factors (API-accessible)
**Format:** JSON (REST API)
**Geographic Scope:** UK
**Update Frequency:** Synced with BEIS/DESNZ releases

**Content:**
- UK BEIS/DESNZ emission factors accessible via API
- Structured JSON format
- Search and filter capabilities
- Integration with Climatiq's emission factor database
- Combines UK government data with standardized API

**Access:** Requires Climatiq API key

---

## Data Ingestion

### Automated Ingestion Script

Use the `ingest_government_emissions.py` script to download and ingest data:

```bash
# List all available sources
python scripts/ingest_government_emissions.py --list

# Ingest all sources
python scripts/ingest_government_emissions.py --sources all

# Ingest specific sources
python scripts/ingest_government_emissions.py --sources UK_DEFRA_2025,EPA_SUPPLY_CHAIN_V13

# Ingest by priority level
python scripts/ingest_government_emissions.py --priority critical
```

### Source IDs

- `UK_DEFRA_2025` - UK DEFRA 2025 GHG Conversion Factors
- `EPA_SUPPLY_CHAIN_V13` - EPA Supply Chain GHG Emission Factors v1.3
- `EPA_GHGRP_2025` - EPA GHGRP Facility Emissions
- `EPA_EMISSION_FACTORS_HUB` - EPA GHG Emission Factors Hub 2025
- `EU_ETS_2024` - EU ETS Verified Emissions
- `EEA_EMISSION_FACTORS` - EEA Emission Factor Database
- `IPCC_EFDB` - IPCC Emission Factor Database
- `IEA_EMISSIONS_2024` - IEA Emissions Factors 2024
- `UK_DEFRA_2024` - UK DEFRA 2024 GHG Conversion Factors
- `CLIMATIQ_BEIS` - Climatiq BEIS Data

### Priority Levels

- **CRITICAL:** Core datasets, updated frequently, high quality
- **HIGH:** Important supplementary data
- **MEDIUM:** Additional context and historical data
- **LOW:** Optional enrichment data

## Data Quality

All government sources are assigned high quality scores (0.85-0.95) in the database due to:
- Official government publication
- Peer-reviewed methodologies
- Regular updates and validation
- Extensive documentation
- Widespread use in compliance reporting

## Geographic Coverage

- **UK:** DEFRA 2025, DEFRA 2024, Climatiq BEIS
- **USA:** EPA Supply Chain v1.3, EPA GHGRP, EPA Emission Factors Hub
- **EU:** EU ETS, EEA Emission Factors
- **Global:** IPCC EFDB, IEA Emissions Factors

## Update Schedule

| Source | Frequency | Typical Release Month |
|--------|-----------|----------------------|
| UK DEFRA | Annual | June |
| EPA Supply Chain | Periodic | Variable |
| EPA GHGRP | Annual | October |
| EPA Emission Factors Hub | Annual | January |
| EU ETS | Annual | April |
| EEA Emission Factors | Periodic | Variable |
| IPCC EFDB | Periodic | Variable |
| IEA Emissions | Annual | October |

## Integration with Parsers

Each data source is processed by specialized parsers that:

1. **Extract** emission factors, facility data, or process information
2. **Map** to Mothra's taxonomy and category hierarchy
3. **Validate** data quality and completeness
4. **Enrich** with geographic scope, metadata, and tags
5. **Store** in the CarbonEntity database with full lineage

See `mothra/agents/parser/` for parser implementations.

## API Access

Some sources provide API access for real-time data retrieval:

- **EPA GHGRP:** https://enviro.epa.gov/enviro/efservice/
- **Climatiq:** https://www.climatiq.io/docs
- **IPCC EFDB (via GHG Protocol):** https://ghgprotocol.org/

## Related Documentation

- [EC3 Integration](ec3_integration.md) - Building materials LCA data
- [Parser Architecture](../mothra/agents/parser/README.md) - Parser system design
- [Database Schema](../mothra/db/README.md) - CarbonEntity and DataSource models

## References

1. UK DESNZ. (2025). Greenhouse gas reporting: conversion factors 2025. GOV.UK.
2. US EPA. (2024). Supply Chain Greenhouse Gas Emission Factors v1.3 by NAICS-6.
3. European Environment Agency. (2024). EU ETS verified emissions data.
4. IPCC. (2019). IPCC Emission Factor Database.
5. International Energy Agency. (2024). Emissions Factors 2024.

---

**For questions or updates, contact the Mothra development team.**
