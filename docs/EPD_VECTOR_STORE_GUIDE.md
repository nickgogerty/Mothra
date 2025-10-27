# EPD Vector Store Loading Guide

This guide explains how to extract all EPD (Environmental Product Declaration) records from the EC3 API, tokenize them, chunk them, and load them into your PostgreSQL vector store for semantic search.

## Overview

The EPD Vector Store Loader pipeline performs the following steps:

1. **Extraction**: Fetches all EPD records from the EC3 (Building Transparency) API with automatic pagination
2. **Parsing**: Converts raw EC3 data into structured `CarbonEntity` and `CarbonEntityVerification` records
3. **Tokenization**: Generates searchable text representations of EPD data
4. **Chunking**: Splits large EPD documents into overlapping chunks (1500 chars with 200 char overlap)
5. **Embedding**: Generates 384-dimensional vector embeddings using `sentence-transformers/all-MiniLM-L6-v2`
6. **Storage**: Persists to PostgreSQL with pgvector extension for fast semantic search

## Prerequisites

### 1. Database Setup

Ensure PostgreSQL with pgvector extension is installed and running:

```bash
# Check PostgreSQL status
pg_isready

# If using Docker
docker-compose up -d postgres
```

### 2. EC3 API Credentials

You need either an API key or OAuth credentials from Building Transparency:

**Option A: API Key** (Recommended)
```bash
export EC3_API_KEY="your_api_key_here"
```

Get your API key from: https://buildingtransparency.org/api

**Option B: OAuth Credentials**
```bash
export EC3_OAUTH_USERNAME="your_username"
export EC3_OAUTH_PASSWORD="your_password"
export EC3_OAUTH_CLIENT_ID="your_client_id"
export EC3_OAUTH_CLIENT_SECRET="your_client_secret"
```

### 3. Python Environment

```bash
# Create virtual environment (if not exists)
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e .
```

## Quick Start

### Load All EPDs (Full Dataset - 90,000+ records)

```bash
./scripts/run_epd_loader.sh
```

This will:
- Fetch all EPD records from EC3 API
- Process in batches of 50
- Generate embeddings for all records
- Store in PostgreSQL with vector index
- Log progress to console and file

**Estimated time**: 4-8 hours depending on network speed and system resources

### Test with Limited Dataset

```bash
# Load first 100 EPDs for testing
./scripts/run_epd_loader.sh --limit 100

# Load 500 EPDs with smaller batch size
python scripts/load_epds_to_vector_store.py --limit 500 --batch-size 25
```

### Skip Already Loaded EPDs

```bash
# Useful for resuming interrupted runs
./scripts/run_epd_loader.sh --skip-existing
```

### Debug Mode

```bash
python scripts/load_epds_to_vector_store.py --limit 10 --log-level DEBUG
```

## Command Line Options

```
Usage: python scripts/load_epds_to_vector_store.py [OPTIONS]

Options:
  --limit N           Limit number of EPDs to process (default: all)
  --batch-size N      Batch size for processing (default: 50)
  --skip-existing     Skip EPDs already in database
  --log-level LEVEL   Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
  --help              Show help message
```

## Configuration

### Chunking Parameters

Edit in the script if needed:

```python
text_chunker = TextChunker(
    chunk_size=1500,        # Characters per chunk
    chunk_overlap=200,      # Overlap between chunks
    max_tokens=512          # Max tokens for embedding model
)
```

### Batch Size

Adjust based on your system resources:

```python
loader = EPDVectorLoader(
    batch_size=50,  # Larger = faster but more memory
    ...
)
```

## Output and Monitoring

### Console Output

The script provides real-time progress:

```
2025-10-27 10:00:00 - INFO - Starting EPD extraction from EC3 API...
2025-10-27 10:00:05 - INFO - EC3 credentials validated successfully
2025-10-27 10:00:10 - INFO - Fetching EPD page 1...
2025-10-27 10:00:15 - INFO - Fetched 100 EPDs (total: 100)
2025-10-27 10:00:20 - INFO - Processing batch 1/900...
2025-10-27 10:00:45 - INFO - Created 15 chunks for entity 1234
2025-10-27 10:01:00 - INFO - Batch committed. Stats: Fetched: 100, Processed: 50, Embedded: 50, Chunks: 245
```

### Log Files

Detailed logs are saved to:
```
epd_vectorization_YYYYMMDD_HHMMSS.log
```

### Statistics

Final summary includes:

- Total EPDs fetched
- Total processed
- Total inserted/updated
- Total embeddings created
- Total chunks generated
- Processing rate (EPDs/sec)
- Errors encountered

## Data Schema

### CarbonEntity

Main entity table storing EPD metadata:

```python
{
    "id": "uuid",
    "source_id": "data_source_id",
    "entity_type": "product",
    "name": "EPD name",
    "description": "Full description",
    "category_hierarchy": ["Materials", "Concrete", "Ready Mix"],
    "geographic_scope": "North America",
    "quality_score": 0.85,
    "embedding": [0.123, -0.456, ...],  # 384-dim vector
    "raw_data": { ... },  # Full EC3 JSON
}
```

### CarbonEntityVerification

Verification and GWP data:

```python
{
    "entity_id": "carbon_entity_id",
    "epd_registration_number": "NEPD-12345-EN",
    "third_party_verified": true,
    "gwp_total": 245.5,  # kg CO2e
    "gwp_co2": 230.0,
    "gwp_ch4": 10.5,
    "gwp_n2o": 5.0,
    "lca_stages_included": ["A1", "A2", "A3"],
    "lca_stage_emissions": {
        "A1-A3": 200.0,
        "A4": 25.0,
        ...
    },
    "environmental_indicators": { ... },
}
```

### DocumentChunk

Text chunks with embeddings:

```python
{
    "entity_id": "carbon_entity_id",
    "chunk_index": 0,
    "total_chunks": 5,
    "chunk_text": "Material: Ready Mix Concrete...",
    "chunk_size": 1500,
    "start_position": 0,
    "end_position": 1500,
    "overlap_before": 0,
    "overlap_after": 200,
    "embedding": [0.789, -0.234, ...],
}
```

## Querying the Vector Store

After loading, you can perform semantic searches:

```python
from mothra.agents.embedding.vector_manager import VectorManager
from mothra.db.session import AsyncSessionLocal

async def search_epds():
    vector_manager = VectorManager()

    async with AsyncSessionLocal() as session:
        # Semantic search
        results = await vector_manager.semantic_search(
            query="low carbon concrete",
            session=session,
            entity_type="product",
            limit=10,
            similarity_threshold=0.7
        )

        for entity, similarity in results:
            print(f"{entity.name} - Similarity: {similarity:.3f}")
            print(f"  GWP: {entity.verification.gwp_total} kg CO2e")
            print()

# Run
import asyncio
asyncio.run(search_epds())
```

### Search with Chunks

For more granular results:

```python
results = await vector_manager.semantic_search_with_chunks(
    query="recycled content steel",
    session=session,
    limit=20
)

for entity, chunk, similarity in results:
    print(f"{entity.name} - Chunk {chunk.chunk_index}/{chunk.total_chunks}")
    print(f"Similarity: {similarity:.3f}")
    print(f"Text: {chunk.chunk_text[:200]}...")
    print()
```

## Troubleshooting

### Authentication Errors

```
ERROR: EC3 API credentials are invalid
```

**Solution**: Verify your credentials:
```bash
# Check environment variables
echo $EC3_API_KEY

# Test authentication manually
curl -H "Authorization: Bearer $EC3_API_KEY" \
  https://buildingtransparency.org/api/epds
```

### Rate Limiting

```
WARNING: Rate limit exceeded
```

**Solution**: The client includes automatic retry with exponential backoff. If issues persist:
- Reduce batch size: `--batch-size 25`
- Add delays between requests (modify script)

### Memory Issues

```
MemoryError: Unable to allocate array
```

**Solution**:
- Reduce batch size: `--batch-size 10`
- Process in smaller chunks: `--limit 1000` then resume with `--skip-existing`

### Database Connection

```
ERROR: could not connect to server
```

**Solution**:
```bash
# Check PostgreSQL is running
pg_isready

# Check connection settings in mothra/config/settings.py
# Verify DATABASE_URL environment variable
echo $DATABASE_URL
```

### pgvector Extension

```
ERROR: type "vector" does not exist
```

**Solution**:
```sql
-- Connect to your database
psql -d mothra

-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify
\dx vector
```

## Performance Tips

### 1. Use Connection Pooling

The script uses SQLAlchemy's async connection pooling automatically.

### 2. Batch Processing

Larger batches = faster but more memory:
- Small systems: `--batch-size 25`
- Medium systems: `--batch-size 50` (default)
- Large systems: `--batch-size 100`

### 3. Parallel Processing

For very large datasets, you can run multiple instances:

```bash
# Terminal 1: Process first 45000 EPDs
python scripts/load_epds_to_vector_store.py --limit 45000 --skip-existing

# Terminal 2: Process remaining (will skip first 45000)
python scripts/load_epds_to_vector_store.py --skip-existing
```

### 4. Index Creation

Create indexes after loading for better query performance:

```sql
-- Already created by Alembic migrations, but verify:
CREATE INDEX IF NOT EXISTS idx_carbon_entities_embedding_hnsw
ON carbon_entities USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw
ON document_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

## Expected Results

For the full EC3 dataset (~90,000 EPDs):

- **Total records**: ~90,000 CarbonEntity records
- **Total chunks**: ~150,000 - 300,000 chunks (depending on EPD size)
- **Total embeddings**: ~240,000 - 390,000 embeddings
- **Database size**: ~5-10 GB (including vectors)
- **Processing time**: 4-8 hours
- **Success rate**: >95% (some EPDs may have incomplete data)

## Next Steps

After loading EPDs into the vector store:

1. **Build Search Interface**: Create API endpoints for semantic search
2. **Fine-tune Embeddings**: Experiment with different embedding models
3. **Optimize Queries**: Adjust similarity thresholds and limits
4. **Add Filters**: Combine vector search with traditional filters (geography, date, etc.)
5. **Monitoring**: Set up dashboards to track usage and performance

## Support

For issues or questions:

1. Check logs: `epd_vectorization_*.log`
2. Review EC3 API docs: https://buildingtransparency.org/api/docs
3. Check pgvector docs: https://github.com/pgvector/pgvector
4. Review code: `scripts/load_epds_to_vector_store.py`

## References

- **EC3 API**: https://buildingtransparency.org/api
- **pgvector**: https://github.com/pgvector/pgvector
- **sentence-transformers**: https://www.sbert.net/
- **EPD International**: https://www.environdec.com/
- **EN 15804 Standard**: https://www.en-standard.eu/bs-en-15804-2012-a2-2019/
