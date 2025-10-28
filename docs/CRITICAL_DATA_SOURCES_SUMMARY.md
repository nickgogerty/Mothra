# Critical Priority Data Sources Summary

This document provides a comprehensive overview of all **critical priority** data sources defined in `mothra/data/sources_catalog.yaml`.

## Overview

MOTHRA tracks **11 critical priority data sources** across three main categories:
- 7 Government APIs & Databases
- 2 LCA Databases
- 2 EPD Registries

These sources form the foundation of the carbon emissions database and are prioritized for daily updates.

---

## Government APIs & Databases (7)

### 1. EPA MOVES (Motor Vehicle Emission Simulator)
- **URL**: https://www.epa.gov/moves
- **Category**: Government
- **Access Method**: API
- **Authentication**: Not required
- **Data Format**: JSON
- **Update Frequency**: Quarterly
- **Rate Limit**: 100 requests/min
- **Size**: ~5 GB
- **Region**: USA
- **Description**: Comprehensive vehicle emission modeling system from the US EPA

### 2. EPA Greenhouse Gas Reporting Program
- **URL**: https://www.epa.gov/ghgreporting
- **Category**: Government
- **Access Method**: REST API
- **Authentication**: Not required
- **Data Format**: JSON
- **Update Frequency**: Annual
- **Rate Limit**: 100 requests/min
- **Size**: ~10 GB
- **Region**: USA
- **Description**: Facility-level greenhouse gas emissions data from large emitters in the United States

### 3. UK DEFRA Conversion Factors
- **URL**: https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting
- **Category**: Government
- **Access Method**: Web scraping
- **Authentication**: Not required
- **Data Format**: XLSX (Excel)
- **Update Frequency**: Annual
- **Size**: ~0.1 GB
- **Region**: UK
- **Description**: Official UK government emission conversion factors for corporate carbon reporting

### 4. EIA (US Energy Information Administration) API
- **URL**: https://www.eia.gov/opendata
- **Category**: Government
- **Access Method**: REST API
- **Authentication**: **Required** (API key)
- **Data Format**: JSON
- **Update Frequency**: Daily
- **Rate Limit**: 5000 requests/day
- **Size**: ~15 GB
- **Region**: USA
- **Description**: Comprehensive US energy statistics including electricity generation and carbon intensity

### 5. IPCC Emission Factor Database
- **URL**: https://www.ipcc-nggip.iges.or.jp/EFDB
- **Category**: Government
- **Access Method**: Web scraping
- **Authentication**: Not required
- **Data Format**: HTML
- **Update Frequency**: Irregular
- **Size**: ~1 GB
- **Region**: Global
- **Description**: International Panel on Climate Change's authoritative emission factor database

### 6. EU Emissions Trading System (ETS) Data
- **URL**: https://ec.europa.eu/clima/ets
- **Category**: Government
- **Access Method**: REST API
- **Authentication**: Not required
- **Data Format**: XML
- **Update Frequency**: Daily
- **Rate Limit**: 100 requests/min
- **Size**: ~8 GB
- **Region**: EU
- **Description**: European Union's carbon market trading data and verified emissions

### 7. ENTSO-E Transparency Platform
- **URL**: https://transparency.entsoe.eu
- **Category**: Government
- **Access Method**: REST API
- **Authentication**: **Required** (API token)
- **Data Format**: XML
- **Update Frequency**: Hourly
- **Rate Limit**: 400 requests/min
- **Size**: ~20 GB
- **Region**: Europe
- **Description**: European electricity generation and cross-border flow data with carbon intensity

---

## LCA (Life Cycle Assessment) Databases (2)

### 8. Ecoinvent Database
- **URL**: https://ecoinvent.org/the-ecoinvent-database
- **Category**: Commercial
- **Access Method**: API
- **Authentication**: **Required** (License needed)
- **Data Format**: JSON
- **Update Frequency**: Quarterly
- **Rate Limit**: 10 requests/min
- **Size**: ~3 GB
- **Region**: Global
- **License**: Commercial license required
- **Description**: Premium life cycle inventory database with 18,000+ datasets covering global supply chains

### 9. USDA LCA Commons
- **URL**: https://www.lcacommons.gov
- **Category**: Government
- **Access Method**: REST API
- **Authentication**: Not required
- **Data Format**: JSON
- **Update Frequency**: Quarterly
- **Rate Limit**: 100 requests/min
- **Size**: ~2 GB
- **Region**: USA
- **Description**: US government's free life cycle assessment database for agriculture, manufacturing, and energy

---

## EPD (Environmental Product Declaration) Registries (2)

### 10. EC3 (Embodied Carbon in Construction Calculator)
- **URL**: https://buildingtransparency.org/ec3
- **Category**: Standards
- **Access Method**: REST API
- **Authentication**: **Required** (OAuth2)
- **Data Format**: JSON
- **Update Frequency**: Continuous
- **Rate Limit**: 1000 requests/min
- **Size**: ~12 GB
- **Region**: Global
- **Description**: Building Transparency's open EPD database with 90,000+ verified environmental product declarations

#### EC3 Endpoints:
- `/api/epds` - 90,000+ Environmental Product Declarations
- `/api/materials` - 50,000+ Construction materials
- `/api/plants` - 10,000+ Manufacturing plant information
- `/api/projects` - 5,000+ Construction projects using EPDs

#### EC3 Resources:
- **API Documentation**: https://buildingtransparency.org/ec3/manage-apps/api-doc/api
- **API Guide**: https://buildingtransparency.org/ec3/manage-apps/api-doc/guide
- **Get API Key**: https://buildingtransparency.org/ec3/manage-apps/keys

---

## Quick Reference Table

| # | Name | Region | Auth Required | Format | Update Freq | Size (GB) |
|---|------|--------|---------------|--------|-------------|-----------|
| 1 | EPA MOVES | USA | No | JSON | Quarterly | 5.0 |
| 2 | EPA GHG Reporting | USA | No | JSON | Annual | 10.0 |
| 3 | UK DEFRA Factors | UK | No | XLSX | Annual | 0.1 |
| 4 | EIA API | USA | Yes | JSON | Daily | 15.0 |
| 5 | IPCC EFDB | Global | No | HTML | Irregular | 1.0 |
| 6 | EU ETS | EU | No | XML | Daily | 8.0 |
| 7 | ENTSO-E | Europe | Yes | XML | Hourly | 20.0 |
| 8 | Ecoinvent | Global | Yes* | JSON | Quarterly | 3.0 |
| 9 | USDA LCA Commons | USA | No | JSON | Quarterly | 2.0 |
| 10 | EC3 | Global | Yes | JSON | Continuous | 12.0 |

*License required

**Total Estimated Size**: ~76 GB for critical sources only

---

## Authentication Requirements

### Sources Requiring API Keys/Tokens:
1. **EIA API** - Free API key from https://www.eia.gov/opendata
2. **ENTSO-E** - Free token from https://transparency.entsoe.eu
3. **EC3** - OAuth2 credentials from https://buildingtransparency.org
4. **Ecoinvent** - Commercial license required

### Configuration:
Store credentials in `.env` file:
```bash
# EIA
EIA_API_KEY=your_eia_api_key

# ENTSO-E
ENTSOE_API_TOKEN=your_entsoe_token

# EC3 OAuth2
EC3_OAUTH_CLIENT_ID=your_client_id
EC3_OAUTH_CLIENT_SECRET=your_client_secret
EC3_OAUTH_USERNAME=your_email
EC3_OAUTH_PASSWORD=your_password

# Ecoinvent (if licensed)
ECOINVENT_API_KEY=your_ecoinvent_key
```

---

## Data Collection Strategy

### Daily Updates (High Velocity)
- EIA API (daily updates)
- EU ETS (daily updates)
- ENTSO-E (hourly updates)
- EC3 (continuous updates)

### Quarterly Updates (Medium Velocity)
- EPA MOVES (quarterly)
- Ecoinvent (quarterly)
- USDA LCA Commons (quarterly)

### Annual Updates (Low Velocity)
- EPA GHG Reporting (annual)
- UK DEFRA Conversion Factors (annual)

### Irregular Updates (Monitor)
- IPCC Emission Factor Database (check monthly)

---

## Priority Crawl Order

For optimal data collection, crawl in this order:

1. **USDA LCA Commons** (free, no auth, good starting dataset)
2. **EPA GHG Reporting** (large US facility data)
3. **UK DEFRA Factors** (essential UK conversion factors)
4. **EPA MOVES** (vehicle emissions baseline)
5. **IPCC EFDB** (global methodology reference)
6. **EIA API** (requires key - rich energy data)
7. **EU ETS** (European market data)
8. **ENTSO-E** (requires token - grid data)
9. **EC3** (requires OAuth - massive EPD dataset)
10. **Ecoinvent** (requires license - premium data)

---

## Database Query

To query these sources from the PostgreSQL database:

```sql
-- List all critical sources
SELECT name, category, priority, status, url, data_format
FROM data_sources
WHERE priority = 'critical'
ORDER BY category, name;

-- Check crawl status
SELECT ds.name, cl.status, cl.records_fetched, cl.completed_at
FROM data_sources ds
LEFT JOIN crawl_logs cl ON ds.id = cl.source_id
WHERE ds.priority = 'critical'
ORDER BY cl.completed_at DESC NULLS LAST;

-- Get authentication requirements
SELECT name, auth_required, access_method, rate_limit
FROM data_sources
WHERE priority = 'critical' AND auth_required = true;
```

---

## Next Steps

1. **Setup Authentication**: Obtain API keys for EIA, ENTSO-E, and EC3
2. **Test Connections**: Verify each API endpoint is accessible
3. **Configure Crawlers**: Set up source-specific parsers for each format (JSON, XML, XLSX, HTML)
4. **Schedule Updates**: Implement appropriate update frequencies
5. **Monitor Quality**: Track data quality scores for each source
6. **Generate Skills**: Use Skill_Seekers to create Claude skills for each source (see SKILL_SEEKERS_INTEGRATION.md)

---

## Related Documentation

- **Full Source Catalog**: `mothra/data/sources_catalog.yaml`
- **Skill_Seekers Integration**: `docs/SKILL_SEEKERS_INTEGRATION.md`
- **Government Data Ingestion**: `docs/GOVERNMENT_DATA_INGESTION_SETUP.md`
- **EC3 Integration Guide**: `EC3_INTEGRATION_GUIDE.md`
- **Database Schema**: `mothra/db/models.py`

---

*Last Updated: 2025-10-28*
*Source: mothra/data/sources_catalog.yaml*
