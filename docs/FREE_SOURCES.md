# Free Public Carbon Data Sources for MOTHRA

This document lists all free, publicly accessible carbon data sources from government agencies, EPD registries, and public institutions that require no authentication or paid licenses.

## Government Sources (No Authentication Required)

### 1. **EPA GHGRP (Greenhouse Gas Reporting Program)**
- **URL**: https://www.epa.gov/ghgreporting
- **Type**: REST API
- **Format**: JSON
- **Coverage**: USA facility-level emissions
- **Update**: Annual
- **Size**: ~10 GB
- **Priority**: CRITICAL

### 2. **UK DEFRA Conversion Factors**
- **URL**: https://www.gov.uk/government/collections/government-conversion-factors-for-company-reporting
- **Type**: Document download
- **Format**: XLSX
- **Coverage**: UK emission factors for all sectors
- **Update**: Annual
- **Size**: ~100 MB
- **Priority**: CRITICAL

### 3. **UK Carbon Intensity API**
- **URL**: https://api.carbonintensity.org.uk
- **Type**: REST API
- **Format**: JSON
- **Coverage**: UK electricity grid carbon intensity
- **Update**: Real-time (30-minute intervals)
- **Size**: ~2 GB
- **Priority**: HIGH
- **Rate Limit**: 3600 requests/hour

### 4. **IPCC Emission Factor Database**
- **URL**: https://www.ipcc-nggip.iges.or.jp/EFDB
- **Type**: Web scraping
- **Format**: HTML
- **Coverage**: Global emission factors from IPCC
- **Update**: Irregular
- **Size**: ~1 GB
- **Priority**: CRITICAL

### 5. **EU Emissions Trading System (ETS)**
- **URL**: https://ec.europa.eu/clima/ets
- **Type**: REST API
- **Format**: XML
- **Coverage**: EU facility-level verified emissions
- **Update**: Daily
- **Size**: ~8 GB
- **Priority**: CRITICAL

### 6. **Australian National Greenhouse Accounts**
- **URL**: https://www.industry.gov.au/data-and-publications/national-greenhouse-accounts-factors
- **Type**: Document download
- **Format**: Excel/PDF
- **Coverage**: Australian emission factors
- **Update**: Annual
- **Size**: ~500 MB
- **Priority**: HIGH

### 7. **EPA MOVES (Motor Vehicle Emissions)**
- **URL**: https://www.epa.gov/moves
- **Type**: API/Database
- **Format**: JSON
- **Coverage**: USA vehicle emissions
- **Update**: Quarterly
- **Size**: ~5 GB
- **Priority**: CRITICAL

### 8. **ISO New England Grid Data**
- **URL**: https://www.iso-ne.com/isoexpress
- **Type**: REST API
- **Format**: JSON
- **Coverage**: New England electricity grid
- **Update**: Hourly
- **Size**: ~3 GB
- **Priority**: MEDIUM

### 9. **CAISO (California ISO) OASIS**
- **URL**: http://oasis.caiso.com
- **Type**: REST API
- **Format**: XML
- **Coverage**: California electricity grid
- **Update**: Hourly
- **Size**: ~4 GB
- **Priority**: MEDIUM

## EPD Registries (No Authentication Required)

### 10. **International EPD System**
- **URL**: https://www.environdec.com/EPD-Search
- **Type**: Web scraping
- **Format**: HTML/PDF
- **Coverage**: Global product environmental declarations
- **Update**: Monthly
- **Size**: ~1 GB
- **Priority**: HIGH

### 11. **IBU EPD Database (Germany)**
- **URL**: https://www.ibu-epd.com/en/published-epds
- **Type**: Web scraping
- **Format**: HTML/PDF
- **Coverage**: German and EU product EPDs
- **Update**: Monthly
- **Size**: ~800 MB
- **Priority**: HIGH

### 12. **EPD Norge (Norway)**
- **URL**: https://www.epd-norge.no
- **Type**: Web scraping
- **Format**: HTML/PDF
- **Coverage**: Norwegian product EPDs
- **Update**: Monthly
- **Size**: ~300 MB
- **Priority**: MEDIUM

### 13. **Australasian EPD Programme**
- **URL**: https://www.epd-australasia.com
- **Type**: Web scraping
- **Format**: HTML/PDF
- **Coverage**: Australia/NZ product EPDs
- **Update**: Monthly
- **Size**: ~200 MB
- **Priority**: MEDIUM

### 14. **FDES INIES (France)**
- **URL**: https://www.inies.fr
- **Type**: Web scraping
- **Format**: HTML/PDF
- **Coverage**: French construction product EPDs
- **Update**: Monthly
- **Size**: ~500 MB
- **Priority**: MEDIUM

## Implementation Priority

### Phase 1: Quick Wins (Easy APIs)
1. ✅ **UK Carbon Intensity API** - Clean JSON, real-time, no auth
2. **EPA GHGRP API** - Well-documented JSON API
3. **ISO New England Grid** - Standard REST API

### Phase 2: Government Emission Factors
4. **UK DEFRA Conversion Factors** - Excel parsing
5. **IPCC Emission Factor Database** - HTML scraping
6. **Australian National Greenhouse Accounts** - Document parsing

### Phase 3: EU & Large Datasets
7. **EU ETS** - XML API with large dataset
8. **EPA MOVES** - Complex database API

### Phase 4: EPD Registries
9. **International EPD System** - PDF extraction
10. **IBU EPD Database** - HTML + PDF
11. **EPD Norge** - HTML + PDF

## Total Estimated Data
- **Volume**: ~50 GB of free, public carbon data
- **Sources**: 14 free sources
- **Coverage**: Global (USA, EU, UK, Australia, International)
- **Update Frequency**: Real-time to Annual

## Notes
- All sources are legally accessible without authentication
- Some sources require respectful rate limiting
- EPD registries require PDF parsing capabilities
- Government APIs are generally well-documented
