# MOTHRA Automated Crawler-Parser Pipeline

The MOTHRA system now features a fully automated pipeline that:
1. **Crawls** data sources
2. **Parses** raw data automatically
3. **Stores** carbon entities in the database
4. **Generates** embeddings for semantic search
5. **Enables** natural language queries

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Survey    │────▶│   Crawler    │────▶│    Parser    │
│    Agent     │     │ Orchestrator │     │   Registry   │
└──────────────┘     └──────────────┘     └──────────────┘
                             │                     │
                             ▼                     ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Raw Data    │     │  Validated   │
                     │   Fetched    │     │   Entities   │
                     └──────────────┘     └──────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │  PostgreSQL  │
                                          │   Database   │
                                          └──────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │  Embedding   │
                                          │    Agent     │
                                          └──────────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │   pgvector   │
                                          │  Similarity  │
                                          │    Search    │
                                          └──────────────┘
```

## Components

### 1. Parser Registry (`parser_registry.py`)

Maps data sources to their appropriate parsers automatically:

```python
from mothra.agents.parser.parser_registry import ParserRegistry

# Automatically selects the right parser
parser = ParserRegistry.get_parser(data_source)

# Check if parser exists
has_parser = ParserRegistry.has_parser(data_source)

# List all available parsers
parsers = ParserRegistry.list_parsers()
```

**Currently Registered Parsers:**
- UK Carbon Intensity API → `UKCarbonIntensityParser`
- UK DEFRA Conversion Factors → `UKDEFRAParser`
- EPA GHGRP → `EPAGHGRPParser`
- EU ETS → `EUETSParser`
- IPCC EFDB → `IPCCEmissionFactorParser`
- International EPD System → `EPDInternationalParser`
- + 5 more EPD registries

### 2. Enhanced Crawler (`crawler_agent.py`)

Now automatically:
1. **Fetches** data via REST API or web scraping
2. **Detects** the appropriate parser from registry
3. **Parses** raw data into validated entities
4. **Stores** entities in PostgreSQL
5. **Logs** statistics (records found, processed, errors)

### 3. Data Flow

```python
# The crawler automatically handles everything:
async with CrawlerOrchestrator() as crawler:
    await crawler.execute_crawl_plan(priority="high")

# Behind the scenes:
# 1. Crawler fetches data from source
# 2. Parser Registry finds the right parser
# 3. Parser extracts and validates entities
# 4. Entities are stored in database
# 5. Ready for embedding generation
```

## Usage

### Test Single Source (UK Carbon Intensity)

```bash
python scripts/test_automated_pipeline.py
```

This will:
- Fetch live UK grid carbon intensity data
- Automatically parse it
- Store entities in database
- Show results and statistics

### Crawl All Active Sources

```bash
python -m mothra.agents.crawler.crawler_agent
```

This will process all sources marked as "active" or "validated" in the database.

### Generate Embeddings

After crawling, generate embeddings for semantic search:

```bash
python -m mothra.agents.embedding.vector_manager
```

### Search the Data

```bash
python scripts/test_search.py
```

Try queries like:
- "UK electricity grid carbon intensity"
- "EPA facility emissions"
- "concrete carbon footprint"
- "natural gas emission factor"

## Adding New Sources

### 1. Create a Parser

```python
from mothra.agents.parser.base_parser import BaseParser

class MySourceParser(BaseParser):
    async def parse(self, data: Any) -> list[dict[str, Any]]:
        entities = []
        for record in data:
            entity = self.create_entity_dict(
                name=record['name'],
                description=record['description'],
                entity_type='process',
                category_hierarchy=['energy', 'fossil_fuels'],
                geographic_scope=['USA'],
                quality_score=0.9,
                # ... additional metadata
            )
            entities.append(entity)
        return entities
```

### 2. Register the Parser

```python
from mothra.agents.parser.parser_registry import ParserRegistry

ParserRegistry.register_parser(
    "My Data Source Name",
    MySourceParser
)
```

### 3. Add Data Source to Catalog

Add to `mothra/data/sources_catalog.yaml`:

```yaml
government_apis:
  - name: "My Data Source Name"
    url: "https://api.example.com/data"
    source_type: "api"
    category: "government"
    priority: "high"
    access_method: "rest"
    auth_required: false
    rate_limit: 100
    data_format: "json"
```

### 4. Run Survey and Crawl

```bash
# Survey discovers new sources
python -m mothra.agents.survey.survey_agent

# Crawler automatically uses your parser
python -m mothra.agents.crawler.crawler_agent
```

## Statistics and Monitoring

The crawler logs detailed statistics:

- **Records Found**: Number of entities parsed from raw data
- **Records Processed**: Number successfully stored in database
- **Duration**: Time taken for crawl + parse + store
- **Status**: success, failed, skipped
- **Errors**: Detailed error messages if parsing fails

View in `crawl_logs` table:

```sql
SELECT
    source_id,
    status,
    records_found,
    records_processed,
    duration_seconds,
    started_at
FROM crawl_logs
ORDER BY started_at DESC
LIMIT 10;
```

## Error Handling

The pipeline handles errors gracefully:

1. **Crawl Failures**: Retry with exponential backoff
2. **Parse Failures**: Log error, continue with next record
3. **Storage Failures**: Log error, continue with next entity
4. **No Parser**: Log warning, skip parsing

Sources with 3+ consecutive errors are marked as "failed" and skipped.

## Performance

- **Concurrent Crawling**: Multiple sources processed in parallel
- **Rate Limiting**: Adaptive rate limiters respect source limits
- **Batch Storage**: Entities committed in batches
- **Async I/O**: Non-blocking database operations

**Typical Performance:**
- UK Carbon Intensity: ~1-2 seconds (fetch + parse + store)
- EPA GHGRP: ~10-30 seconds (large dataset)
- EPD scraping: ~5-15 seconds per page

## Next Steps

1. **Transform Agent**: Normalize units and standardize data
2. **Quality Agent**: Score and validate data quality
3. **Scheduler**: Automatic periodic crawling
4. **Monitoring**: Grafana dashboards for pipeline health

## Example Output

```
================================================================================
MOTHRA Automated Crawler-Parser Pipeline Test
================================================================================

Parser Registry
================================================================================

Registered parsers: 11
  1. UK Carbon Intensity API
     → UKCarbonIntensityParser
  2. EPA GHGRP
     → EPAGHGRPParser
  3. EU ETS
     → EUETSParser
  ...

================================================================================
Step 1: Setup Data Source
================================================================================
✅ Using existing data source: UK Carbon Intensity API
✅ Parser available: UKCarbonIntensityParser

Entities in database before crawl: 42

================================================================================
Step 2: Run Automated Crawler Pipeline
================================================================================
Fetching data → Parsing → Storing...

✅ Crawl complete: UK Carbon Intensity API
✅ Parsed 2 entities
✅ Stored 2 entities

================================================================================
Step 3: Results
================================================================================

Crawl Log
================================================================================
Status: success
Duration: 1.23s
Records Found: 2
Records Processed: 2

New Entities Created: 2
================================================================================

1. UK Grid Carbon Intensity 2024-10-25T16:00Z
   Type: energy
   Category: energy > electricity > grid > uk
   Geographic Scope: UK
   Quality Score: 0.95
   Description: UK electricity grid carbon intensity from 2024-10-25T16:00Z...

2. UK Grid Carbon Intensity 2024-10-25T16:30Z
   Type: energy
   Category: energy > electricity > grid > uk
   Geographic Scope: UK
   Quality Score: 0.95
   Description: UK electricity grid carbon intensity from 2024-10-25T16:30Z...

✅ Pipeline Complete!
   Entities before: 42
   Entities after: 44
   New entities: 2
```
