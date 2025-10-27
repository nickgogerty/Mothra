# MOTHRA EC3 Integration Guide

## Overview

MOTHRA now integrates with **EC3 (Embodied Carbon in Construction Calculator)**, the world's largest open database of Environmental Product Declarations (EPDs) for construction materials, maintained by Building Transparency.

### What is EC3?

**EC3** provides free access to:
- **90,000+ digital EPDs** from verified manufacturers
- **Construction material carbon footprints** across all major categories
- **Full LCA data** compliant with EN 15804+A2
- **Third-party verified** environmental impacts
- **Global coverage** with regional specificity

**Categories Available:**
- Concrete (ready-mix, precast, blocks, CLT)
- Steel (structural, rebar, decking, profiles)
- Wood (lumber, engineered wood, panels, CLT)
- Insulation (mineral wool, foam, cellulose, natural)
- Glass (glazing, curtain walls, IGUs)
- Aluminum (extrusions, cladding, windows)
- Gypsum (drywall, plaster, boards)
- Roofing (membranes, tiles, metal)
- Flooring (carpet, hardwood, LVT, ceramic)
- Sealants & Adhesives

### Why This Matters

EPDs are the **gold standard** for construction carbon accounting:
- Required for **LEED v4+** certification (up to 3 points)
- Mandated by **EU Green Public Procurement**
- Used in **carbon border adjustment** mechanisms
- Essential for **whole building LCA** (ISO 21931)
- Basis for **material EPD benchmarks**

## Professional Verification Standards

MOTHRA's EC3 integration captures data meeting professional verification requirements from:
- **TÜV SÜD** (Technischer Überwachungsverein)
- **DNV GL** (Det Norske Veritas)
- **SGS** (Société Générale de Surveillance)
- **UL Environment**
- **NSF International**

### Supported Standards

#### ISO 14067:2018
**Greenhouse gases — Carbon footprint of products**
- Partial PCF (A1-A3 minimum)
- Complete PCF (A1-D if applicable)
- Declared unit and functional unit
- System boundaries
- Allocation procedures

#### ISO 14064-1/2/3
**GHG inventories and verification**
- Scope 1: Direct emissions
- Scope 2: Purchased energy
- Scope 3: Value chain (15 categories)
- Biogenic carbon (separate reporting)
- Uncertainty quantification

#### GHG Protocol
**Corporate and Product Standards**
- Organizational boundaries
- Operational control approach
- Cradle-to-gate minimum
- Full value chain encouraged

#### EN 15804+A2:2019
**EPDs for construction products (European Standard)**

**Product Stage (A1-A3):**
- A1: Raw material supply
- A2: Transport to manufacturer
- A3: Manufacturing

**Construction Stage (A4-A5):**
- A4: Transport to building site
- A5: Installation into building

**Use Stage (B1-B7):**
- B1: Use
- B2: Maintenance
- B3: Repair
- B4: Replacement
- B5: Refurbishment
- B6: Operational energy use
- B7: Operational water use

**End of Life (C1-C4):**
- C1: Deconstruction/demolition
- C2: Transport to waste processing
- C3: Waste processing
- C4: Disposal

**Benefits and Loads Beyond Building (Module D):**
- Reuse, recovery, recycling potential
- Exported energy
- Reported separately (not added to A-C)

#### ISO 21930:2017
**Core rules for environmental product declarations of construction products and services**
- Mandatory indicators (GWP, ODP, AP, EP, POCP)
- Optional indicators (resource use, waste)
- Data quality requirements
- Validity period (5 years typical)

## Database Schema

### CarbonEntityVerification Table

Stores comprehensive verification data for each carbon entity:

```python
class CarbonEntityVerification(Base):
    # Core Identification
    entity_id: UUID  # Foreign key to carbon_entities

    # GHG Protocol & ISO 14064
    ghg_scopes: list[str]  # ["scope_1", "scope_2", "scope_3", "biogenic"]
    scope_3_categories: list[str]  # ["1", "2", "3", ... "15"]

    # LCA Stages (EN 15804)
    lca_stages_included: list[str]  # ["A1", "A2", "A3", "D"]
    lca_stage_emissions: dict  # {"A1": 12.5, "A2": 3.2, "A3": 8.7, "D": -2.1}

    # EPD Specific
    epd_registration_number: str  # "EPD-ABC-20240001-CBG1-EN"
    epd_program_operator: str  # "IBU", "EPD Norge", "Environdec"
    pcr_reference: str  # "EN 15804+A2:2019"
    declared_unit: str  # "1 m³", "1 kg", "1 m²"
    functional_unit: str  # "1 m² of wall, R-value 3.5"
    reference_service_life: int  # Years (e.g., 60 for concrete)

    # GWP by Gas Type (kg CO2e per declared unit)
    gwp_total: float  # Total global warming potential
    gwp_co2: float  # CO2 contribution
    gwp_ch4: float  # Methane contribution
    gwp_n2o: float  # Nitrous oxide contribution
    gwp_biogenic: float  # Biogenic carbon (separate per EN 15804)

    # Verification
    verification_status: str  # "verified", "pending", "expired"
    verification_standards: list[str]  # ["ISO 14067:2018", "EN 15804+A2"]
    verification_body: str  # "TUV SUD", "DNV GL", "SGS"
    verification_date: datetime
    valid_from: date
    valid_until: date

    # Data Quality (ISO 14044)
    data_quality_rating: str  # "excellent", "good", "fair"
    temporal_representativeness: str  # "2023", "2020-2023"
    geographic_representativeness: str  # "EU-27", "USA", "Global"
    technological_representativeness: str  # "Specific technology", "Industry average"

    # System Boundaries
    system_boundary: str  # "cradle-to-gate", "cradle-to-grave"
    allocation_method: str  # "physical", "economic", "cut-off"

    # Product Classification
    unspsc_code: str  # UN Standard Products and Services Code
    cas_number: str  # Chemical Abstracts Service number
    cpc_code: str  # Central Product Classification

    # EC3 Integration
    ec3_material_id: str  # EC3 internal material ID
    openepd_id: str  # OpenEPD globally unique ID

    # Compliance Flags
    iso_14067_compliant: bool
    iso_14064_compliant: bool
    en_15804_compliant: bool
    ghg_protocol_compliant: bool
    third_party_verified: bool
```

### Scope3Category Reference Table

Maps GHG Protocol Scope 3 category numbers to descriptions:

```python
class Scope3Category(Base):
    category_number: int  # 1-15
    category_name: str
    description: str
    upstream_downstream: str  # "upstream" or "downstream"
```

**15 Scope 3 Categories:**

**Upstream (1-8):**
1. Purchased goods and services
2. Capital goods
3. Fuel and energy related activities (not in Scope 1/2)
4. Upstream transportation and distribution
5. Waste generated in operations
6. Business travel
7. Employee commuting
8. Upstream leased assets

**Downstream (9-15):**
9. Downstream transportation and distribution
10. Processing of sold products
11. Use of sold products
12. End-of-life treatment of sold products
13. Downstream leased assets
14. Franchises
15. Investments

## Getting Started

### 1. Authentication (Choose One Method)

MOTHRA supports three authentication methods for EC3 API access:

#### Method 1: API Key (Bearer Token) - **RECOMMENDED**

**Simplest method for most users.**

While public access works for basic queries, an API key provides:
- Higher rate limits (1000 req/hour vs 100)
- Access to all EPDs (some may be restricted)
- Priority support
- No expiration

**Get your key:**
1. Visit: https://buildingtransparency.org/ec3/manage-apps/keys
2. Create free account (or log in)
3. Click "Generate New API Key"
4. Copy your key

**Set environment variable:**
```bash
export EC3_API_KEY="your-api-key-here"

# Or add to .env file
echo "EC3_API_KEY=your-api-key-here" >> .env
```

**Usage in code:**
```python
from mothra.agents.discovery.ec3_integration import EC3Client

# Automatically uses EC3_API_KEY from environment
async with EC3Client() as client:
    results = await client.search_epds(category="Concrete", limit=100)
```

#### Method 2: OAuth 2.0 Password Grant

**For programmatic access with username/password.**

This method uses OAuth 2.0 Resource Owner Password Credentials flow to obtain an access token.

**Configuration:**
```bash
# Set OAuth credentials in environment
export EC3_OAUTH_GRANT_TYPE="password"
export EC3_CLIENT_ID="your_client_id"
export EC3_CLIENT_SECRET="your_client_secret"
export EC3_USERNAME="your_username"
export EC3_PASSWORD="your_password"
```

**Usage in code:**
```python
from mothra.agents.discovery.ec3_integration import EC3Client
import os

oauth_config = {
    "grant_type": "password",
    "client_id": os.getenv("EC3_CLIENT_ID"),
    "client_secret": os.getenv("EC3_CLIENT_SECRET"),
    "username": os.getenv("EC3_USERNAME"),
    "password": os.getenv("EC3_PASSWORD"),
}

async with EC3Client(oauth_config=oauth_config) as client:
    results = await client.search_epds(category="Steel", limit=100)
    # Token is automatically acquired and refreshed
```

**Token details:**
- Token endpoint: `https://buildingtransparency.org/api/oauth2/token`
- Token lifetime: 3600 seconds (1 hour)
- Automatic refresh: Yes (handled by client)
- Scope: `read write`

#### Method 3: OAuth 2.0 Authorization Code Grant

**For applications with user authorization flow.**

This method uses the standard OAuth 2.0 Authorization Code flow with user consent.

**Step 1: Get authorization code** (redirect user to):
```
https://buildingtransparency.org/oauth/authorize?
  response_type=code&
  client_id=YOUR_CLIENT_ID&
  redirect_uri=YOUR_REDIRECT_URI&
  scope=read
```

**Step 2: Exchange code for token:**
```python
from mothra.agents.discovery.ec3_integration import EC3Client

oauth_config = {
    "grant_type": "authorization_code",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "code": "authorization_code_from_step_1",
}

async with EC3Client(oauth_config=oauth_config) as client:
    results = await client.search_epds(category="Wood", limit=100)
```

#### Authentication Features

All authentication methods include:
- ✅ **Automatic token refresh** - Expired tokens are automatically renewed
- ✅ **401 handling** - Client detects token expiry and re-authenticates
- ✅ **Retry logic** - Network failures trigger exponential backoff
- ✅ **Error logging** - Authentication issues are logged clearly

**Comparison:**

| Feature | API Key | OAuth Password | OAuth Auth Code |
|---------|---------|----------------|-----------------|
| Setup complexity | Simple | Medium | Complex |
| User interaction | None | None | Required |
| Token expiry | Never | 1 hour (auto-refresh) | 1 hour (auto-refresh) |
| Use case | Scripts, automation | Programmatic access | Web apps |
| **Recommended for** | **Most users** | Server applications | User-facing apps |

### 2. Initialize Database

Ensure PostgreSQL with pgvector is running:

```bash
# Start PostgreSQL (if using Docker)
docker-compose up -d postgres

# Initialize database schema
python -c "
import asyncio
from mothra.db.session import init_db
asyncio.run(init_db())
"
```

This creates:
- `carbon_entities` table (main entity storage)
- `carbon_entity_verification` table (verification data)
- `scope3_categories` table (reference data)
- `document_chunks` table (for chunking large descriptions)
- Vector indexes for semantic search

### 3. Test EC3 Connection

Run the integration test suite:

```bash
python scripts/test_ec3_integration.py
```

**Expected output:**
```
================================================================================
EC3 INTEGRATION TEST SUITE
================================================================================

Testing EC3 (Embodied Carbon in Construction Calculator) integration
with Building Transparency's openEPD API

Database: 90,000+ verified construction material EPDs

⚠️  EC3_API_KEY not set
   Using public access (limited)

🔧 Initializing database...
✅ Database ready

================================================================================
TEST 1: EC3 API Connection
================================================================================
✅ Successfully connected to EC3 API
   Retrieved 5 EPDs (total available: 12,456)

================================================================================
TEST 2: EPD Parsing
================================================================================
Parsing EPD: Ready Mix Concrete 4000 PSI

✅ Successfully parsed EPD
   Name: Ready Mix Concrete 4000 PSI
   Category: ['material', 'construction', 'concrete']
   Entity Type: material
   LCA Stages: ['A1', 'A2', 'A3', 'D']
   EPD Number: EPD-ABC-20240001-CBG1-EN
   Verified: True

================================================================================
TEST 3: EPD Import Pipeline
================================================================================
Before import:
  Total entities: 0
  Verified entities: 0

Importing 10 Concrete EPDs from EC3...

✅ Import completed
   EPDs imported: 10
   Errors: 0

After import:
  Total entities: 10 (+10)
  Verified entities: 10 (+10)

================================================================================
TEST 4: Verification Data Storage
================================================================================
✅ Found verified entity:
   Name: Ready Mix Concrete 4000 PSI
   Source: EC3 Building Transparency

   Verification Details:
   - Status: verified
   - Standards: ['EN 15804+A2', 'ISO 14067:2018']
   - GHG Scopes: ['scope_1', 'scope_2']
   - LCA Stages: ['A1', 'A2', 'A3', 'D']
   - EPD Number: EPD-ABC-20240001-CBG1-EN
   - ISO 14067: True
   - EN 15804: True
   - Third Party: True

   LCA Stage Emissions (kg CO2e):
     A1: 125.3
     A2: 8.7
     A3: 42.1
     D: -12.5

================================================================================
TEST SUMMARY
================================================================================

✅ PASSED - EC3 Connection
✅ PASSED - EPD Parsing
✅ PASSED - EPD Import
✅ PASSED - Verification Data

================================================================================
Results: 4/4 tests passed
================================================================================

🎉 All tests passed! EC3 integration is working correctly.
```

## Importing EPDs

### Interactive Import Script

The easiest way to import EPDs is using the interactive script:

```bash
python scripts/import_ec3_epds.py
```

**Interactive prompts:**

```
================================================================================
MOTHRA - EC3 EPD Importer
================================================================================

Importing verified Environmental Product Declarations
from EC3 (Building Transparency) database

EC3 Database: 90,000+ EPDs for construction materials

🔧 Initializing database...
✅ Database ready

Initial state: 0 entities
Existing EPDs: 0

================================================================================
Importing EPDs by Category
================================================================================

Import all categories? (y/n) [default: y]: y
EPDs per category? [default: 50]: 100

📦 Importing category: Concrete
   Limit: 100 EPDs
   ✅ Imported: 98
   ❌ Errors: 2
   ⏱️  Duration: 12.3s

📦 Importing category: Steel
   Limit: 100 EPDs
   ✅ Imported: 100
   ❌ Errors: 0
   ⏱️  Duration: 15.7s

... (continues for all categories)

================================================================================
📊 EC3 EPD IMPORT SUMMARY
================================================================================

┌─ Import Results by Category ─────────────────────────────────────┐
│ Concrete             │ Imported:   98 │ Errors:  2 │  12.3s │
│ Steel                │ Imported:  100 │ Errors:  0 │  15.7s │
│ Wood                 │ Imported:   87 │ Errors:  0 │  11.2s │
│ Insulation           │ Imported:   95 │ Errors:  1 │  13.8s │
│ Glass                │ Imported:   42 │ Errors:  0 │   6.1s │
│ Aluminum             │ Imported:   78 │ Errors:  0 │  10.4s │
│ Gypsum               │ Imported:   34 │ Errors:  0 │   5.2s │
│ Roofing              │ Imported:   56 │ Errors:  0 │   7.9s │
│ Flooring             │ Imported:   45 │ Errors:  0 │   6.8s │
│ Sealants             │ Imported:   23 │ Errors:  0 │   3.7s │
├───────────────────────────────────────────────────────────────────┤
│ TOTAL                │ Imported:  658 │ Errors:  3 │         │
└───────────────────────────────────────────────────────────────────┘

┌─ Database Statistics ────────────────────────────────────────────┐
│ Total Entities Before:             0                           │
│ Total Entities After:            658                           │
│ New EPD Entities:                658                           │
│ Total EPDs in Database:          658                           │
│ Verified Entities:               658                           │
└──────────────────────────────────────────────────────────────────┘

┌─ Data Quality ───────────────────────────────────────────────────┐
│ Verification Rate:              100.0%                          │
│ EN 15804 Compliant:               658 (all EC3 EPDs)               │
│ Third-Party Verified:             658 (all EC3 EPDs)               │
└──────────────────────────────────────────────────────────────────┘

================================================================================
🎉 EC3 EPD Import Complete!
================================================================================

Total Duration: 93.1s (1.6 minutes)

📖 Next Steps:
1. Generate embeddings: python scripts/chunk_and_embed_all.py
2. Test semantic search on EPD data
3. Query by material category or manufacturer
4. Explore LCA stages and carbon footprints

💡 Example Queries:
   - "low carbon concrete ready mix"
   - "CLT cross laminated timber"
   - "recycled steel rebar"
   - "mineral wool insulation"

================================================================================
```

### Programmatic Import

For automation or custom workflows:

```python
import asyncio
from mothra.agents.discovery.ec3_integration import import_epds_from_ec3

async def import_concrete_epds():
    """Import concrete EPDs."""
    result = await import_epds_from_ec3(
        category="Concrete",
        limit=100
    )

    print(f"Imported: {result['epds_imported']}")
    print(f"Errors: {result['errors']}")

asyncio.run(import_concrete_epds())
```

## Querying Verification Data

### SQL Examples

**Get all verified concrete EPDs with LCA data:**

```sql
SELECT
    e.name,
    e.description,
    v.epd_registration_number,
    v.lca_stages_included,
    v.lca_stage_emissions,
    v.gwp_total,
    v.verification_body,
    v.valid_until
FROM carbon_entities e
JOIN carbon_entity_verification v ON e.id = v.entity_id
WHERE
    e.category_hierarchy @> ARRAY['concrete']
    AND v.verification_status = 'verified'
    AND v.en_15804_compliant = true
ORDER BY v.gwp_total ASC
LIMIT 10;
```

**Find EPDs with Module D benefits (recycling potential):**

```sql
SELECT
    e.name,
    v.lca_stage_emissions->>'D' as module_d_benefit,
    v.gwp_total,
    v.epd_registration_number
FROM carbon_entities e
JOIN carbon_entity_verification v ON e.id = v.entity_id
WHERE
    v.lca_stage_emissions ? 'D'
    AND (v.lca_stage_emissions->>'D')::float < 0  -- Negative = benefit
ORDER BY (v.lca_stage_emissions->>'D')::float ASC
LIMIT 20;
```

**EPDs expiring in next 6 months:**

```sql
SELECT
    e.name,
    v.epd_registration_number,
    v.valid_until,
    v.verification_body
FROM carbon_entities e
JOIN carbon_entity_verification v ON e.id = v.entity_id
WHERE
    v.valid_until BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '6 months'
ORDER BY v.valid_until ASC;
```

### Python Examples

**Find low-carbon concrete with EN 15804 compliance:**

```python
from sqlalchemy import select
from mothra.db.models import CarbonEntity
from mothra.db.models_verification import CarbonEntityVerification
from mothra.db.session import get_db_context

async def find_low_carbon_concrete():
    async with get_db_context() as db:
        stmt = (
            select(CarbonEntity, CarbonEntityVerification)
            .join(
                CarbonEntityVerification,
                CarbonEntity.id == CarbonEntityVerification.entity_id
            )
            .where(
                CarbonEntity.category_hierarchy.contains(["concrete"]),
                CarbonEntityVerification.en_15804_compliant == True,
                CarbonEntityVerification.gwp_total < 200  # kg CO2e/m³
            )
            .order_by(CarbonEntityVerification.gwp_total)
            .limit(10)
        )

        result = await db.execute(stmt)

        for entity, verification in result:
            print(f"{entity.name}")
            print(f"  GWP: {verification.gwp_total} kg CO2e")
            print(f"  EPD: {verification.epd_registration_number}")
            print(f"  LCA Stages: {verification.lca_stages_included}")
            print()
```

**Calculate total embodied carbon for a building:**

```python
async def calculate_building_carbon(material_quantities: dict):
    """
    Calculate building carbon footprint.

    material_quantities: {
        "concrete": 1500,  # m³
        "steel": 50000,     # kg
        "insulation": 500,  # m²
    }
    """
    total_gwp = 0
    breakdown = {}

    async with get_db_context() as db:
        for material, quantity in material_quantities.items():
            # Get average GWP for material category
            stmt = select(
                func.avg(CarbonEntityVerification.gwp_total)
            ).join(
                CarbonEntity,
                CarbonEntity.id == CarbonEntityVerification.entity_id
            ).where(
                CarbonEntity.category_hierarchy.contains([material]),
                CarbonEntityVerification.verification_status == "verified"
            )

            avg_gwp = await db.scalar(stmt)

            if avg_gwp:
                material_total = avg_gwp * quantity
                total_gwp += material_total
                breakdown[material] = {
                    "quantity": quantity,
                    "avg_gwp": avg_gwp,
                    "total": material_total
                }

    return {
        "total_gwp_kg_co2e": total_gwp,
        "breakdown": breakdown
    }
```

## Semantic Search Integration

After importing EPDs, generate embeddings for semantic search:

```bash
# Generate embeddings for all entities
python scripts/chunk_and_embed_all.py
```

**Search examples:**

```python
from mothra.agents.embedding.vector_manager import VectorManager

manager = VectorManager()

# Search for low-carbon concrete
results = await manager.semantic_search_with_chunks(
    query="low carbon concrete with recycled content high strength",
    limit=10,
    similarity_threshold=0.7
)

for result in results:
    print(f"{result['name']} (similarity: {result['similarity']:.3f})")
    print(f"  Category: {result['category_hierarchy']}")
    print(f"  Source: {result['source_id']}")
    print(f"  Match via: {result['match_types']}")  # 'entity', 'chunk', or both
```

## Data Quality and Validation

### EPD Quality Indicators

All EC3 EPDs include:

✅ **Third-party verification** by accredited bodies
✅ **EN 15804+A2 compliance** for construction products
✅ **ISO 14067:2018** carbon footprint methodology
✅ **PCR compliance** (Product Category Rules)
✅ **Data quality ratings** per ISO 14044
✅ **Temporal validity** (typical 5-year lifecycle)
✅ **Geographic specificity** (country/region level)
✅ **Technology representativeness** (specific or average)

### Validation Checklist

Before using EPD data for compliance:

- [ ] Verify EPD is not expired (`valid_until > current_date`)
- [ ] Check geographic scope matches project location
- [ ] Confirm LCA stages align with project needs (e.g., A1-A3 minimum)
- [ ] Validate declared unit matches quantity takeoff
- [ ] Review PCR reference for product category match
- [ ] Check verification body is accredited
- [ ] Ensure technology is representative of product

### Common Issues

**Issue**: EPD expired
**Solution**: Search for updated EPD from same manufacturer or use industry average

**Issue**: Geographic mismatch (EU EPD for US project)
**Solution**: Apply regional adjustment factors or find local equivalent

**Issue**: Incomplete LCA stages (only A1-A3)
**Solution**: Acceptable for material procurement decisions; use separate transport/installation data for full building LCA

**Issue**: Different declared units (1 m³ vs 1 kg)
**Solution**: Convert using material density from EPD technical data

## Advanced Features

### Benchmarking

Compare product against industry average:

```python
async def benchmark_product(entity_id: UUID):
    """Compare product GWP to category average."""
    async with get_db_context() as db:
        # Get product
        entity = await db.get(CarbonEntity, entity_id)
        verification = await db.scalar(
            select(CarbonEntityVerification).where(
                CarbonEntityVerification.entity_id == entity_id
            )
        )

        # Get category average
        avg_stmt = select(
            func.avg(CarbonEntityVerification.gwp_total)
        ).join(
            CarbonEntity,
            CarbonEntity.id == CarbonEntityVerification.entity_id
        ).where(
            CarbonEntity.category_hierarchy.contains(entity.category_hierarchy[:2])
        )

        category_avg = await db.scalar(avg_stmt)

        if verification and category_avg:
            delta_pct = ((verification.gwp_total - category_avg) / category_avg) * 100

            return {
                "product": entity.name,
                "gwp": verification.gwp_total,
                "category_average": category_avg,
                "delta_percent": delta_pct,
                "performance": "better" if delta_pct < 0 else "worse"
            }
```

### Material Substitution Analysis

Find lower-carbon alternatives:

```python
async def find_alternatives(current_material_id: UUID, max_gwp_delta: float = 0.8):
    """
    Find lower-carbon alternatives to current material.

    max_gwp_delta: Maximum GWP as fraction of current (0.8 = 20% reduction)
    """
    async with get_db_context() as db:
        # Get current material
        current = await db.get(CarbonEntity, current_material_id)
        current_verif = await db.scalar(
            select(CarbonEntityVerification).where(
                CarbonEntityVerification.entity_id == current_material_id
            )
        )

        if not current_verif:
            return []

        target_gwp = current_verif.gwp_total * max_gwp_delta

        # Find alternatives in same category with lower GWP
        stmt = (
            select(CarbonEntity, CarbonEntityVerification)
            .join(
                CarbonEntityVerification,
                CarbonEntity.id == CarbonEntityVerification.entity_id
            )
            .where(
                CarbonEntity.category_hierarchy.contains(current.category_hierarchy[:2]),
                CarbonEntity.id != current_material_id,
                CarbonEntityVerification.gwp_total <= target_gwp,
                CarbonEntityVerification.verification_status == "verified"
            )
            .order_by(CarbonEntityVerification.gwp_total)
            .limit(10)
        )

        result = await db.execute(stmt)

        alternatives = []
        for entity, verif in result:
            reduction = ((current_verif.gwp_total - verif.gwp_total) /
                        current_verif.gwp_total) * 100

            alternatives.append({
                "name": entity.name,
                "gwp": verif.gwp_total,
                "reduction_percent": reduction,
                "epd_number": verif.epd_registration_number
            })

        return alternatives
```

### Scope 3 Category Analysis

Analyze value chain emissions:

```python
async def analyze_scope3(entity_id: UUID):
    """Analyze Scope 3 emissions by category."""
    async with get_db_context() as db:
        verif = await db.scalar(
            select(CarbonEntityVerification).where(
                CarbonEntityVerification.entity_id == entity_id
            )
        )

        if not verif or not verif.scope_3_categories:
            return {}

        # Get category descriptions
        categories_stmt = select(Scope3Category).where(
            Scope3Category.category_number.in_(
                [int(c) for c in verif.scope_3_categories]
            )
        )

        result = await db.execute(categories_stmt)
        categories = {c.category_number: c for c in result.scalars()}

        return {
            "scope_3_categories": [
                {
                    "number": int(cat_num),
                    "name": categories[int(cat_num)].category_name,
                    "type": categories[int(cat_num)].upstream_downstream
                }
                for cat_num in verif.scope_3_categories
            ]
        }
```

## Integration with Other Data Sources

MOTHRA can combine EC3 EPDs with other data sources:

### EPA GHGRP (Facility-Level)
- **EC3**: Product-level embodied carbon (materials)
- **EPA**: Facility-level operational emissions (manufacturing)
- **Combined**: Complete Scope 1+2+3 analysis

### UK DEFRA Conversion Factors
- **EC3**: Construction materials (detailed LCA)
- **DEFRA**: Transport, energy, waste (simplified factors)
- **Combined**: Full project lifecycle assessment

### Custom EPD Upload
- Parse company-specific EPDs
- Map to same verification schema
- Compare against EC3 benchmarks

## Compliance Reporting

Generate reports meeting various standards:

### LEED v4+ Materials & Resources

```python
async def generate_leed_report():
    """Generate LEED MR Credit compliance report."""
    async with get_db_context() as db:
        stmt = (
            select(CarbonEntity, CarbonEntityVerification)
            .join(
                CarbonEntityVerification,
                CarbonEntity.id == CarbonEntityVerification.entity_id
            )
            .where(
                CarbonEntityVerification.en_15804_compliant == True,
                CarbonEntityVerification.third_party_verified == True
            )
        )

        result = await db.execute(stmt)

        products = []
        for entity, verif in result:
            products.append({
                "product_name": entity.name,
                "manufacturer": entity.metadata.get("manufacturer"),
                "epd_number": verif.epd_registration_number,
                "verification_body": verif.verification_body,
                "valid_until": verif.valid_until,
                "compliant": (
                    verif.en_15804_compliant and
                    verif.third_party_verified and
                    verif.valid_until > date.today()
                )
            })

        return {
            "total_products": len(products),
            "compliant_products": sum(1 for p in products if p["compliant"]),
            "products": products
        }
```

### ISO 14067 Product Carbon Footprint

```python
async def generate_iso14067_report(entity_id: UUID):
    """Generate ISO 14067 compliant PCF report."""
    async with get_db_context() as db:
        entity = await db.get(CarbonEntity, entity_id)
        verif = await db.scalar(
            select(CarbonEntityVerification).where(
                CarbonEntityVerification.entity_id == entity_id
            )
        )

        return {
            # Product identification
            "product_name": entity.name,
            "declared_unit": verif.declared_unit,
            "functional_unit": verif.functional_unit,

            # GHG emissions
            "gwp_total_kg_co2e": verif.gwp_total,
            "gwp_fossil": verif.gwp_co2 + verif.gwp_ch4 + verif.gwp_n2o,
            "gwp_biogenic": verif.gwp_biogenic,

            # System boundary
            "system_boundary": verif.system_boundary,
            "lca_stages": verif.lca_stages_included,
            "allocation_method": verif.allocation_method,

            # Data quality
            "temporal_representativeness": verif.temporal_representativeness,
            "geographic_representativeness": verif.geographic_representativeness,
            "data_quality_rating": verif.data_quality_rating,

            # Verification
            "iso_14067_compliant": verif.iso_14067_compliant,
            "verification_body": verif.verification_body,
            "verification_date": verif.verification_date,
            "valid_period": f"{verif.valid_from} to {verif.valid_until}"
        }
```

## Next Steps

### Immediate

1. **Test Integration**: Run `python scripts/test_ec3_integration.py`
2. **Import Sample Data**: Import 10-50 EPDs per category
3. **Generate Embeddings**: Run `python scripts/chunk_and_embed_all.py`
4. **Test Search**: Query for materials by type and carbon performance

### Short Term

1. **Full Import**: Import 1,000+ EPDs across all categories
2. **Benchmark Analysis**: Compare products against category averages
3. **Alternative Finding**: Build material substitution recommendations
4. **API Development**: Create REST endpoints for EPD queries

### Long Term

1. **Real-Time Sync**: Schedule daily EC3 updates for new EPDs
2. **Custom PCR Mapping**: Map company PCRs to standard categories
3. **LCA Automation**: Auto-calculate building carbon from BIM models
4. **Compliance Automation**: Generate LEED, BREEAM, DGNB reports

## Resources

### Official Documentation
- **EC3 Platform**: https://buildingtransparency.org/ec3/
- **OpenEPD API**: https://docs.buildingtransparency.org/
- **API Keys**: https://buildingtransparency.org/ec3/manage-apps/keys

### Standards
- **EN 15804+A2:2019**: https://www.en-standard.eu/bs-en-15804-2012-a2-2019/
- **ISO 14067:2018**: https://www.iso.org/standard/71206.html
- **ISO 14064-1:2018**: https://www.iso.org/standard/66453.html
- **GHG Protocol**: https://ghgprotocol.org/

### EPD Programs
- **International EPD System**: https://www.environdec.com/
- **IBU (Germany)**: https://ibu-epd.com/
- **EPD Norge**: https://www.epd-norge.no/
- **FDES INIES (France)**: https://www.inies.fr/

## Support

For issues with:
- **MOTHRA EC3 Integration**: Check this guide and test scripts
- **EC3 API**: Contact Building Transparency support
- **EPD Interpretation**: Consult verification body or PCR authors
- **Standards Compliance**: Engage accredited LCA professionals

## Success Metrics

After implementing EC3 integration, you should have:

✅ Access to 90,000+ verified construction material EPDs
✅ Professional verification data (TUV, DNV, SGS standards)
✅ EN 15804+A2 LCA stages (A1-D) for all products
✅ ISO 14067 and GHG Protocol compliance fields
✅ Semantic search across material carbon footprints
✅ Benchmarking and alternative finding capabilities
✅ LEED/BREEAM compliance reporting
✅ Full value chain (Scope 1+2+3) emissions tracking

**The EC3 integration makes MOTHRA production-ready for professional carbon verification and construction industry compliance!** 🎉
