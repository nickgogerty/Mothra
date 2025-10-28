# EIA (Energy Information Administration) Integration

## Overview

The EIA integration enables MOTHRA to ingest energy and emissions data from the U.S. Energy Information Administration's Open Data API v2. This integration provides access to:

- **15,000+ power plant facilities** with fuel consumption and emissions data
- **State-level CO2 emissions** by sector and fuel type (1960-present)
- **Electricity generation data** by state and fuel source
- **Carbon coefficients** and emission factors

## Quick Start

### 1. Get an API Key

1. Visit https://www.eia.gov/opendata/
2. Click "Register" and create a free account
3. Your API key will be provided immediately (no approval needed)
4. Copy your API key

### 2. Configure API Key

Add your API key to the `.env` file in the project root:

```bash
EIA_API_KEY=your_api_key_here
```

### 3. Run Ingestion

**Ingest all high-volume data (fastest path to 15K+ records):**
```bash
python scripts/ingest_eia_data.py --all
```

**Test with a small dataset first:**
```bash
python scripts/ingest_eia_data.py --all --max-records 100
```

**Ingest specific endpoints:**
```bash
# Only facility data
python scripts/ingest_eia_data.py --facility --max-records 5000

# Only CO2 emissions aggregates
python scripts/ingest_eia_data.py --emissions --max-records 5000
```

**Filter by state:**
```bash
# California data only
python scripts/ingest_eia_data.py --all --states CA

# Multiple states
python scripts/ingest_eia_data.py --all --states CA,NY,TX
```

## Architecture

### Components

#### 1. EIA API Client (`mothra/agents/discovery/eia_integration.py`)

The `EIAClient` class handles all API interactions:

```python
from mothra.agents.discovery.eia_integration import EIAClient

async with EIAClient() as client:
    # Get facility data
    facilities = await client.get_facility_fuel_data(
        state_ids=["CA"],
        frequency="annual",
        max_records=1000
    )

    # Get CO2 emissions
    emissions = await client.get_co2_emissions_aggregates(
        state_ids=["CA"],
        max_records=1000
    )
```

**Features:**
- Automatic API key loading from environment
- Exponential backoff retry logic (2s, 4s, 8s, 16s delays)
- Rate limiting awareness (handles 429 errors)
- Pagination support (up to 5000 records per request)
- Generic endpoint access via `get_endpoint()`

#### 2. EIA Parser (`mothra/agents/parser/eia_parser.py`)

The `EIAParser` class transforms raw API responses into standardized `CarbonEntity` records:

```python
from mothra.agents.parser.eia_parser import EIAParser

parser = EIAParser(source)
entities = await parser.parse(api_response_data)
```

**Parsing capabilities:**
- Power plant facility records
- State-level CO2 emissions aggregates
- Electricity generation records
- Generic EIA data formats

**Data enrichment:**
- Geographic scope mapping (USA, USA-CA, etc.)
- Category hierarchy assignment
- Quality score calculation (0.85-0.9 for EIA data)
- Custom tagging (eia, power_plant, state codes, fuel types)

#### 3. Ingestion Script (`scripts/ingest_eia_data.py`)

Command-line tool for batch data ingestion:
- Creates/updates `DataSource` records
- Fetches data via `EIAClient`
- Parses data via `EIAParser`
- Stores entities in PostgreSQL
- Creates `CrawlLog` entries for tracking
- Provides progress logging and statistics

### Data Flow

```
1. User runs: python scripts/ingest_eia_data.py --all
                            ↓
2. EIADataIngestion creates/finds DataSource records
                            ↓
3. EIAClient fetches data from API with pagination
                            ↓
4. EIAParser transforms JSON → CarbonEntity dicts
                            ↓
5. Entities stored in PostgreSQL (batch commits)
                            ↓
6. CrawlLog updated with statistics
```

## API Endpoints

### Available Endpoints

| Endpoint | Route | Records | Description |
|----------|-------|---------|-------------|
| **Facility Fuel** | `/electricity/facility-fuel/data` | 15,000+ | Power plant fuel consumption and emissions |
| **CO2 Emissions** | `/co2-emissions/co2-emissions-aggregates/data` | 5,000+ | State-level emissions by sector/fuel |
| **Generation** | `/electricity/electric-power-operational-data/data` | 10,000+ | Electricity generation by state/fuel |
| **RTO Fuel Mix** | `/electricity/rto/fuel-type-data/data` | 1,000+ | Real-time regional grid fuel mix |

### Data Frequencies

- **Annual**: Full year data (default for most endpoints)
- **Monthly**: Month-by-month breakdowns
- **Quarterly**: Quarterly aggregates
- **Hourly**: Real-time data (select endpoints)

## Database Schema

### DataSource Records

EIA integration creates `DataSource` records with:

```python
{
    "name": "EIA Facility Data",
    "url": "https://api.eia.gov/v2/electricity/facility-fuel/data",
    "source_type": "api",
    "category": "government",
    "access_method": "rest",
    "auth_required": True,
    "rate_limit": 100,  # requests per minute
    "priority": "high",
    "status": "active"
}
```

### CarbonEntity Records

Example power plant entity:

```python
{
    "name": "Example Power Plant - Coal (2023)",
    "entity_type": "process",
    "category_hierarchy": ["energy", "coal", "fossil_fuel"],
    "geographic_scope": ["USA", "USA-TX"],
    "quality_score": 0.9,
    "custom_tags": ["eia", "power_plant", "tx", "coal"],
    "extra_metadata": {
        "plant_code": "12345",
        "plant_name": "Example Power Plant",
        "state": "TX",
        "fuel_type": "Coal",
        "consumption": 123456.7,
        "consumption_units": "MMBtu",
        "generation": 12345,
        "generation_units": "MWh",
        "period": "2023"
    }
}
```

Example state emissions entity:

```python
{
    "name": "California - Electric Power CO2 Emissions from Coal (2023)",
    "entity_type": "process",
    "category_hierarchy": ["energy", "electricity", "power_sector"],
    "geographic_scope": ["USA", "USA-CA"],
    "quality_score": 0.9,
    "custom_tags": ["eia", "co2_emissions", "state_data", "ca"],
    "extra_metadata": {
        "state_id": "CA",
        "sector_id": "ELE",
        "fuel_id": "COW",
        "emissions_value": 12345.67,
        "units": "million metric tons CO2",
        "period": "2023"
    }
}
```

## Performance

### Expected Record Counts

| Endpoint | Max Records | Typical Fetch Time |
|----------|-------------|-------------------|
| Facility Fuel (all states, annual) | 15,000+ | 3-5 minutes |
| CO2 Emissions (all states, 1960-2023) | 10,000+ | 2-3 minutes |
| **Total (both endpoints)** | **25,000+** | **5-8 minutes** |

### Rate Limiting

- EIA doesn't publish official limits, but testing shows ~100 req/min is safe
- Client includes exponential backoff on 429 (rate limit) responses
- Pagination limited to 5000 records per request (EIA maximum)

### Optimization Tips

1. **Use state filters** to reduce data volume:
   ```bash
   python scripts/ingest_eia_data.py --all --states CA,NY,TX
   ```

2. **Limit records** for testing:
   ```bash
   python scripts/ingest_eia_data.py --all --max-records 1000
   ```

3. **Ingest incrementally** by endpoint:
   ```bash
   python scripts/ingest_eia_data.py --facility --max-records 10000
   python scripts/ingest_eia_data.py --emissions --max-records 10000
   ```

## Error Handling

### Common Issues

**1. Missing API Key**
```
Error: No API key provided - requests may fail or be rate limited
```
**Solution:** Set `EIA_API_KEY` environment variable or add to `.env`

**2. Rate Limiting**
```
WARNING: eia_rate_limited - attempt 1, delay 2s
```
**Solution:** Client automatically retries with exponential backoff. No action needed.

**3. Network Errors**
```
ERROR: eia_request_exception - ClientError
```
**Solution:** Client retries up to 4 times. Check network connectivity if persistent.

**4. Database Connection**
```
ERROR: entity_storage_failed
```
**Solution:** Verify PostgreSQL is running and database credentials are correct.

## Testing

### Unit Test EIA Client

```python
from mothra.agents.discovery.eia_integration import EIAClient
import asyncio

async def test():
    async with EIAClient() as client:
        # Test with small dataset
        facilities = await client.get_facility_fuel_data(
            state_ids=["CA"],
            max_records=10
        )
        print(f"Fetched {len(facilities)} facility records")

        emissions = await client.get_co2_emissions_aggregates(
            state_ids=["CA"],
            max_records=10
        )
        print(f"Fetched {len(emissions)} emission records")

asyncio.run(test())
```

### Integration Test

Run the built-in test in the EIA client:

```bash
cd /home/user/Mothra
python -m mothra.agents.discovery.eia_integration
```

## Configuration

### Settings (`mothra/config/settings.py`)

```python
class Settings(BaseSettings):
    # EIA API Configuration
    eia_api_key: str | None = None
    eia_rate_limit: int = 100  # requests per minute
```

### Environment Variables

```bash
# Required
EIA_API_KEY=your_api_key_here

# Optional
EIA_API_BASE_URL=https://api.eia.gov/v2  # Override base URL
EIA_RATE_LIMIT=100  # Custom rate limit
```

## Monitoring

### Crawl Logs

Each ingestion creates `CrawlLog` entries:

```sql
SELECT
    source_id,
    status,
    records_found,
    records_processed,
    records_inserted,
    duration_seconds,
    created_at
FROM crawl_logs
WHERE source_id IN (
    SELECT id FROM data_sources WHERE name LIKE 'EIA%'
)
ORDER BY created_at DESC;
```

### Entity Counts

```sql
SELECT
    ds.name,
    COUNT(ce.id) as entity_count,
    AVG(ce.quality_score) as avg_quality_score
FROM carbon_entities ce
JOIN data_sources ds ON ce.source_uuid = ds.id
WHERE ds.name LIKE 'EIA%'
GROUP BY ds.name;
```

## Maintenance

### Updating Data

Re-run ingestion periodically to get latest data:

```bash
# Monthly update (recommended)
python scripts/ingest_eia_data.py --all

# Update specific states
python scripts/ingest_eia_data.py --all --states CA,NY,TX
```

### Data Freshness

- **Facility data**: Updated monthly by EIA
- **CO2 emissions**: Annual updates (historical data)
- **Generation data**: Updated monthly/quarterly

## References

- **EIA Open Data Portal**: https://www.eia.gov/opendata/
- **API Documentation**: https://www.eia.gov/opendata/documentation.php
- **API Dashboard**: https://www.eia.gov/opendata/browser/
- **Data FAQs**: https://www.eia.gov/opendata/faqs.php
- **Get API Key**: https://www.eia.gov/opendata/ (free registration)

## Support

For issues or questions:
1. Check logs in `mothra/logs/` directory
2. Review `CrawlLog` entries in database
3. Enable debug logging: `LOG_LEVEL=DEBUG` in `.env`
4. Consult EIA API documentation for endpoint-specific issues
