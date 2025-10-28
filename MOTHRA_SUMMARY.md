# MOTHRA Carbon Database - Summary Report

**Generated:** 2025-10-28

---

## Executive Summary

MOTHRA is a comprehensive carbon emissions database system designed to aggregate, validate, and serve emissions factors from 100+ authoritative data sources worldwide. The system combines government databases, LCA datasets, EPD registries, and scientific literature into a unified, semantically searchable repository.

---

## 1. Data Sources Overview

### Critical Priority Sources (11 Major Sources)

MOTHRA is configured to track **100+ data sources** with the following critical ones prioritized for daily updates:

#### Government APIs & Databases (7 sources)
1. **EPA MOVES** - Vehicle emission modeling system (~5 GB)
2. **EPA GHGRP** - Greenhouse Gas Reporting Program with 16,000+ large US facility emissions (~10 GB)
3. **UK DEFRA Conversion Factors** - Official UK government GHG conversion factors (~0.1 GB)
4. **EIA API** - US Energy Information Administration comprehensive energy data (~15 GB)
5. **IPCC Emission Factor Database** - Authoritative global emission factors from IPCC reports (~1 GB)
6. **EU ETS Data** - European Emissions Trading System verified emissions from 16,000+ installations (~8 GB)
7. **ENTSO-E Transparency Platform** - European electricity grid carbon intensity data (~20 GB)

#### LCA Databases (2 sources)
8. **Ecoinvent Database** - Premium LCA database with 18,000+ datasets covering global industrial processes (~3 GB, requires license)
9. **USDA LCA Commons** - US government's free LCA data repository (~2 GB)

#### EPD Registries (2+ sources)
10. **EC3 (Building Transparency)** - 90,000+ verified Environmental Product Declarations (~12 GB)
11. **Additional EPD Systems:**
    - International EPD System
    - IBU Environmental Product Declarations
    - EPD Norge (Norwegian EPD)
    - Australasian EPD Programme

### Additional Source Categories
- Real-time carbon intensity APIs (UK, multiple grids)
- National greenhouse gas inventories (Australia, Canada, etc.)
- Industry-specific databases (construction materials, fuels, etc.)
- Research publications and academic sources
- Commercial LCA databases and tools

**Total Database Size Target:** 50+ GB
**Total Entity Target:** 100,000+ carbon entities

---

## 2. Database Schema & Data Structure

### Core Tables

#### `carbon_entities` - Main Carbon Data Repository
**Purpose:** Stores all carbon-related processes, materials, products, and services

**Key Fields:**
- `id`: UUID primary key
- `entity_type`: process | material | product | service | energy
- `name`: Entity name
- `description`: Detailed description
- `category_hierarchy`: ARRAY(String) - Hierarchical taxonomy classifications
- `isic_code`, `naics_code`, `unspsc_code`: Industry classification codes
- `geographic_scope`: ARRAY(String) - Geographic applicability
- `temporal_validity`: DATERANGE - Time period validity
- `quality_score`: Float (0-1) - Data quality assessment
- `confidence_level`: Float (0-1) - Confidence in data
- `embedding`: Vector(384) - Semantic search embedding (all-MiniLM-L6-v2)
- `source_uuid`: Reference to data source
- `raw_data`: JSON - Original data structure
- Timestamps: `created_at`, `updated_at`, `last_verified_at`

#### `emission_factors` - Emissions Factor Data
**Purpose:** Stores GHG emission factors linked to carbon entities

**Key Fields:**
- `entity_id`: Link to CarbonEntity
- `value`: Float - Emission factor value
- `unit`: String - Unit of measurement (e.g., "kgCO2e/kg", "kgCO2e/kWh")
- `scope`: Integer - GHG Protocol scope (1, 2, or 3)
- `scope_3_category`: String - Specific Scope 3 category (15 categories)
- `lifecycle_stage`: String - cradle | gate | grave | use
- `calculation_method`: Text - How the factor was derived
- `accounting_standard`: String - ISO14040 | PAS2050 | GHG_Protocol | ISO14067
- `uncertainty_min`, `uncertainty_max`: Float - Uncertainty range
- `uncertainty_distribution`: String - Statistical distribution type
- `geographic_scope`: ARRAY(String)
- `temporal_scope`: DATERANGE
- `quality_score`: Float (0-1)
- `data_quality_flags`: JSON - Quality indicators
- `embedding`: Vector(384) - Semantic search

#### `carbon_entity_verification` - Professional Verification Data
**Purpose:** Stores third-party verified EPD and carbon footprint data

**Compliance Standards:**
- ISO 14067:2018 (Product Carbon Footprint)
- ISO 14064-1/2/3 (GHG Verification)
- GHG Protocol (Scope 1, 2, 3 with 15 categories)
- EN 15804+A2:2019 (EPD LCA Stages)
- ISO 21930:2017 (Construction EPD)

**Key Fields:**
- `entity_id`: Link to CarbonEntity
- `verification_status`: draft | submitted | verified | expired
- `verification_body`: Organization that performed verification
- `verification_date`, `expiry_date`
- `epd_registration_number`, `epd_program_operator`
- `ghg_scopes`: ARRAY(String) - Scope 1, 2, 3, biogenic
- `scope_3_categories`: 15 GHG Protocol categories
- `lca_stages_included`: EN 15804 stages (A1-A5, B1-B7, C1-C4, Module D)
- **GWP Values (Global Warming Potential):**
  - `gwp_total`: Total GWP in kg CO2e
  - `gwp_co2`, `gwp_ch4`, `gwp_n2o`: Individual gas contributions
  - `gwp_hfcs`, `gwp_pfcs`, `gwp_sf6`, `gwp_nf3`: Fluorinated gases
  - `gwp_biogenic`: Biogenic carbon
  - `gwp_luluc`: Land Use & Land Use Change
- **Environmental Indicators (JSON):**
  - ODP: Ozone Depletion Potential
  - AP: Acidification Potential
  - EP: Eutrophication Potential
  - POCP: Photochemical Ozone Creation Potential
  - ADP: Abiotic Depletion Potential
  - WDP: Water Depletion Potential
- `iso_14067_compliant`, `en_15804_compliant`, `ghg_protocol_compliant`, `third_party_verified`: Boolean flags
- `data_quality_indicators`: JSON - Per ISO 14044

#### `document_chunks` - Large Document Chunking
**Purpose:** Enables semantic search across large documents (reports, standards, etc.)

**Key Fields:**
- `entity_id`: Reference to parent CarbonEntity
- `chunk_index`, `total_chunks`: Position in document
- `chunk_text`: Text content of chunk
- `chunk_size`: Size in characters
- `start_position`, `end_position`: Position in original document
- `overlap_before`, `overlap_after`: Overlap with adjacent chunks
- `embedding`: Vector(384) - Individual chunk embedding
- `relevance_score`: Float - Chunk importance/relevance

#### `data_sources` - Source Catalog
**Purpose:** Tracks all configured data sources and their status

**Key Fields:**
- `name`, `url`: Source identification
- `source_type`: database | api | file | scrape
- `category`: government | standards | research | commercial
- `priority`: critical | high | medium | low
- `access_method`: rest | graphql | scrape | download
- `auth_required`: Boolean - Requires authentication
- `rate_limit`: Integer - Requests per minute
- `update_frequency`: realtime | hourly | daily | weekly | monthly | annual
- `data_format`: json | xml | csv | excel | pdf | html
- `status`: discovered | validated | active | inactive | failed
- `last_crawled`, `last_successful_crawl`
- `error_count`, `consecutive_failures`

#### `crawl_logs` - Data Ingestion Audit Trail
**Purpose:** Tracks all data collection operations for monitoring and debugging

**Key Fields:**
- `source_id`: Reference to DataSource
- `started_at`, `completed_at`, `duration_seconds`
- `status`: running | completed | failed | partial
- `records_found`, `records_fetched`: Discovery counts
- `records_processed`, `records_inserted`, `records_updated`, `records_failed`: Processing stats
- `error_message`, `error_details`: Failure information
- `data_size_mb`: Size of data processed
- `quality_score_avg`: Average quality of ingested data

#### `process_relationships` - Entity Relationships
**Purpose:** Links related carbon entities for process chains and substitutions

**Key Fields:**
- `source_entity_id`, `target_entity_id`: Entity links
- `relationship_type`: parent | child | substitute | equivalent | complement
- `weight`: Float - Relationship strength/quantity
- `confidence`: Float - Confidence in relationship

#### `scope3_categories` - GHG Protocol Reference Data
**Purpose:** Reference table for 15 Scope 3 categories with standardized definitions

**Categories:**
1. Purchased goods and services
2. Capital goods
3. Fuel- and energy-related activities
4. Upstream transportation and distribution
5. Waste generated in operations
6. Business travel
7. Employee commuting
8. Upstream leased assets
9. Downstream transportation and distribution
10. Processing of sold products
11. Use of sold products
12. End-of-life treatment of sold products
13. Downstream leased assets
14. Franchises
15. Investments

---

## 3. Emissions Factor Types Tracked

### Supply Chain Emissions Factors
- **EPA Supply Chain GHG Emission Factors** v1.3
  - 1,016 commodity-specific factors
  - Organized by NAICS-6 industry codes
  - Includes upstream Scope 3 emissions
  - Covers materials, products, services, and logistics

### Conversion Factors
- **UK DEFRA Conversion Factors** (Annual updates)
  - Fuels (solid, liquid, gaseous)
  - Electricity (by country, by grid)
  - Transport (by mode, vehicle type, distance)
  - Refrigerants & other GHGs
  - Water supply & wastewater treatment
  - Waste disposal & material recycling
  - Materials & goods

### IPCC Emission Factors
- Energy production and consumption
- Industrial processes and product use (IPPU)
- Agriculture, Forestry, and Other Land Use (AFOLU)
- Waste management
- Direct and indirect GHG emissions

### Facility-Level Emissions
- **EPA GHGRP:** 16,000+ US facilities with:
  - Annual GHG emissions by scope
  - Industry sector (NAICS)
  - Geographic location (lat/lon)
  - Parent company information

- **EU ETS:** 16,000+ European installations with:
  - Verified annual emissions
  - Allowances allocated vs. actual emissions
  - Installation operator details
  - Sector classification

### Product-Level Data (EPDs)
- **EC3 Database:** 90,000+ verified EPDs with:
  - Product category (UN CPC, MasterFormat)
  - Declared unit (m³, kg, m², ton, etc.)
  - Lifecycle stages (A1-A3: Production, A4: Transport, C1-C4: End-of-life, D: Beyond lifecycle)
  - GWP per declared unit
  - Manufacturer and plant location
  - PCR (Product Category Rules) used
  - Verification body and date

---

## 4. Data Quality & Standards

### Quality Scoring System (0.0 - 1.0)
**Factors considered:**
- Data source authority and reputation
- Verification status (third-party verified = higher score)
- Data completeness (all required fields populated)
- Temporal relevance (recent data = higher score)
- Geographic specificity (site-specific > country > global)
- Methodology transparency (documented method = higher)
- Uncertainty quantification (lower uncertainty = higher)

**Quality Thresholds:**
- Minimum quality score: 0.7
- Minimum confidence level: 0.8
- Deduplication similarity: 0.95

### Compliance Standards Support
- ✅ **ISO 14067:2018** - Carbon footprint of products
- ✅ **ISO 14064-1:2018** - GHG inventories at organization level
- ✅ **ISO 14064-2:2019** - GHG inventories at project level
- ✅ **ISO 14064-3:2019** - GHG verification and validation
- ✅ **ISO 14040/14044** - Life Cycle Assessment
- ✅ **GHG Protocol Corporate Standard** - Scope 1, 2, 3 accounting
- ✅ **GHG Protocol Product Standard** - Product carbon footprints
- ✅ **EN 15804+A2:2019** - EPD core rules for construction
- ✅ **ISO 21930:2017** - Construction EPD framework
- ✅ **PAS 2050:2011** - Product lifecycle emissions

---

## 5. System Architecture

### Multi-Agent Ingestion System
```
Orchestrator Agent
├── Discovery Agent
│   ├── Source discovery & validation
│   ├── Known dataset configuration
│   └── Automated source cataloging
│
├── Crawler Agent
│   ├── Concurrent data collection (max 10 concurrent)
│   ├── Rate limiting (50-100 req/min)
│   ├── Retry logic (3 attempts with exponential backoff)
│   └── Progress monitoring
│
├── Parser Agents
│   ├── EPAGHGRPParser - Facility emissions
│   ├── EUETSParser - EU trading system
│   ├── UKDEFRAParser - UK conversion factors
│   ├── IPCCEmissionFactorParser - IPCC data
│   ├── EPDInternationalParser - EPD declarations
│   ├── JSONParser, XMLParser, CSVParser - Generic formats
│   └── Auto-detection and format-specific handling
│
├── Quality Agent
│   ├── Data validation & quality scoring
│   ├── Completeness checking
│   ├── Outlier detection
│   └── Uncertainty quantification
│
├── Transform Agent
│   ├── Taxonomy mapping (ISIC, NAICS, UNSPSC)
│   ├── Unit normalization
│   ├── Geographic standardization (ISO 3166)
│   └── Temporal scope extraction
│
└── Embedding Agent
    ├── Semantic indexing (384-dim vectors)
    ├── Chunk embedding for large documents
    └── Similarity computation for deduplication
```

### Technology Stack
- **Database:** PostgreSQL 16 with pgvector extension
- **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Caching:** Redis 7
- **Monitoring:** Prometheus + Grafana
- **Languages:** Python 3.11+ with async/await
- **Key Libraries:**
  - SQLAlchemy (async ORM)
  - asyncpg (PostgreSQL driver)
  - sentence-transformers (embeddings)
  - httpx (async HTTP client)
  - beautifulsoup4 (web scraping)
  - pandas (data processing)

---

## 6. Query Capabilities

### Search Methods
1. **Exact Match:** By entity name, ID, or classification codes
2. **Category Search:** By taxonomy hierarchies
3. **Geographic Search:** By country, region, or facility location
4. **Semantic Search:** Vector similarity search using embeddings
5. **Filtered Search:** Combined filters (type, quality, date range, source)
6. **Relationship Traversal:** Follow process chains and substitutes

### Performance Targets
- Query latency: <100ms (P95 target ~80ms)
- Concurrent queries: 1,000+ QPS
- Embedding generation: ~50ms per document
- Batch import: 10,000+ entities per minute

---

## 7. Data Update Strategies

### Update Frequencies by Source Type
- **Real-time:** Grid carbon intensity APIs (UK, ENTSO-E)
- **Daily:** Critical government APIs (EPA, EU ETS updates)
- **Weekly:** Medium-priority commercial sources
- **Monthly:** Static databases (Ecoinvent, USDA LCA Commons)
- **Annual:** Standards and guidelines (IPCC, DEFRA factors)

### Automated Workflows
- **Daily update cron:** 2:00 AM (0 2 * * *)
- **Weekly refresh cron:** 2:00 AM Sundays (0 2 * * SUN)
- **Monitoring:** Prometheus metrics + Grafana dashboards
- **Error handling:** Automatic retries with exponential backoff
- **Quality gates:** New data must meet minimum quality thresholds

---

## 8. Access & Authentication

### Required API Keys/Credentials
1. **EIA API:** Requires API key (free registration)
2. **EC3 API:** API key + OAuth2 for privileged endpoints
3. **ENTSO-E:** Security token required
4. **Ecoinvent:** License required (commercial)
5. **Most government sources:** Open access, no authentication

### Configuration
All credentials stored in `.env` file:
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mothra
POSTGRES_USER=mothra
POSTGRES_PASSWORD=changeme

# EC3 OAuth2
EC3_OAUTH_CLIENT_ID=your_client_id
EC3_OAUTH_CLIENT_SECRET=your_secret
EC3_OAUTH_USERNAME=your_email
EC3_OAUTH_PASSWORD=your_password

# Other APIs
EIA_API_KEY=your_eia_key
ENTSO_E_TOKEN=your_entso_e_token
```

---

## 9. Data Volume Estimates

### Current Targets
| Metric | Target Value |
|--------|--------------|
| Total Entities | 100,000+ |
| Verified EPDs | 90,000+ (from EC3) |
| Facility Records | 32,000+ (EPA + EU) |
| Emission Factors | 50,000+ |
| Data Sources | 100+ |
| Database Size | 50+ GB |
| Embeddings | 100,000 vectors (384-dim) |

### Breakdown by Source Type
- **EPDs (EC3):** ~90,000 entities (~12 GB)
- **EPA GHGRP:** ~16,000 facilities (~10 GB)
- **EU ETS:** ~16,000 installations (~8 GB)
- **EPA Supply Chain:** ~1,016 commodity factors
- **UK DEFRA:** ~5,000 conversion factors
- **IPCC:** ~10,000 emission factors
- **Ecoinvent:** ~18,000 LCI datasets (~3 GB)
- **Other sources:** ~20,000 entities

---

## 10. Typical Use Cases

### Carbon Accounting
- **Corporate GHG Inventories:** Scope 1, 2, 3 calculations
- **Product Carbon Footprints:** ISO 14067 compliant
- **Supply Chain Emissions:** Upstream and downstream tracking
- **Facility Benchmarking:** Compare against similar facilities

### LCA & Sustainability
- **Life Cycle Assessment:** Cradle-to-grave impact analysis
- **EPD Generation:** Data for creating new EPDs
- **Material Selection:** Compare alternatives with verified data
- **Circular Economy:** End-of-life and recycling factors

### Compliance & Reporting
- **Regulatory Reporting:** EPA, EU ETS, CDP submissions
- **Sustainability Reporting:** GRI, SASB, TCFD
- **Carbon Disclosure:** Scope 3 Category 1-15 breakdowns
- **Green Claims Substantiation:** Verified third-party data

### Research & Analysis
- **Climate Science:** Emissions factor validation
- **Policy Analysis:** Sectoral emission trends
- **Technology Assessment:** Compare low-carbon alternatives
- **Market Intelligence:** Industry-specific carbon intensity

---

## 11. Running the Summary Report

### Prerequisites
```bash
# Start database services
docker-compose up -d postgres redis

# Wait for database to be ready
docker-compose exec postgres pg_isready -U mothra
```

### Generate Summary
```bash
# Run the summary script
python -m scripts.database_summary

# Or directly
python scripts/database_summary.py
```

### Expected Output
The script generates a comprehensive report showing:
1. **Overview:** Total entities, verified EPDs, data sources, verification rate
2. **By Data Source:** Count of entities per source with type and category
3. **By Entity Type:** Breakdown of process, material, product, service, energy
4. **By Category:** Top 20 categories from taxonomy hierarchies
5. **By Geography:** Top 15 geographic scopes
6. **Quality Metrics:** Average quality score, embedding coverage
7. **Verification Details:** Status breakdown, verification bodies, compliance stats, GWP statistics
8. **Storage Metrics:** Approximate database size
9. **Progress to Goals:** Visual progress bar to 100K entity target
10. **Recommendations:** Next steps for data population and system improvement

---

## 12. Key Files & Locations

### Database Schema
- **Core Models:** `/mothra/db/models.py`
- **Verification Models:** `/mothra/db/models_verification.py`
- **Chunking Models:** `/mothra/db/models_chunks.py`

### Data Ingestion
- **Orchestrator:** `/mothra/agents/orchestrator/`
- **Parsers:** `/mothra/agents/parser/`
- **Discovery:** `/mothra/agents/discovery/dataset_discovery.py`

### Configuration
- **Settings:** `/mothra/config/settings.py`
- **Source Catalog:** `/mothra/data/sources_catalog.yaml`
- **Docker Compose:** `/docker-compose.yml`

### Scripts
- **Summary Report:** `/scripts/database_summary.py`
- **Bulk Import:** `/scripts/bulk_import_epds.py`
- **Embedding Generation:** `/scripts/chunk_and_embed_all.py`
- **Search Testing:** `/scripts/test_search.py`

### Documentation
- **Installation:** `/INSTALL.md`, `/QUICKSTART.md`
- **Data Growth:** `/GROWING_THE_DATASET.md`
- **EC3 Integration:** `/EC3_INTEGRATION_GUIDE.md`
- **Deep Crawl:** `/DEEP_CRAWL_GUIDE.md`

---

## Summary Statistics at Full Capacity

| Metric | Value |
|--------|-------|
| **Total Data Sources** | 100+ |
| **Critical Daily Sources** | 11 |
| **Target Entities** | 100,000+ |
| **Verified EPDs Available** | 90,000+ |
| **Facility Emissions Tracked** | 32,000+ (US + EU) |
| **Emission Factor Database Size** | 50,000+ factors |
| **Geographic Coverage** | 200+ countries |
| **Industry Sectors** | 1,000+ (NAICS/ISIC) |
| **Embedding Dimension** | 384 (all-MiniLM-L6-v2) |
| **Query Performance Target** | <100ms P95 |
| **Database Size Target** | 50+ GB |
| **Standards Compliance** | 10+ (ISO, GHG Protocol, EN, PAS) |
| **Update Frequency** | Real-time to Annual |

---

## Quick Reference: What's in MOTHRA?

**Data Types:**
- ✅ Emission factors (50,000+ planned)
- ✅ Facility-level emissions (32,000+)
- ✅ Product EPDs (90,000+)
- ✅ LCA datasets (18,000+ from Ecoinvent)
- ✅ Grid carbon intensity (real-time)
- ✅ Supply chain factors (1,016 commodities)
- ✅ Conversion factors (5,000+ UK DEFRA)

**Geographic Coverage:**
- 🌍 Global (IPCC, Ecoinvent, EC3)
- 🇺🇸 United States (EPA, EIA)
- 🇬🇧 United Kingdom (DEFRA, Carbon Intensity)
- 🇪🇺 European Union (EU ETS, ENTSO-E)
- 🌏 + Australia, Canada, and 200+ countries

**Verification Status:**
- ✅ Third-party verified EPDs
- ✅ Government-published factors
- ✅ Peer-reviewed research
- ✅ ISO/EN standard compliant

**Search Capabilities:**
- 🔍 Semantic search (AI-powered)
- 🏷️ Category/taxonomy search
- 🌍 Geographic filtering
- ⭐ Quality-filtered results
- 🔗 Relationship traversal

---

**For more information, see:**
- Main README: `/README.md`
- Getting Started: `/QUICKSTART.md`
- Growing the Dataset: `/GROWING_THE_DATASET.md`
- EC3 Integration: `/EC3_INTEGRATION_GUIDE.md`
