# Complete EPD Loading Guide
## Loading All EPDs into Vector Store with Full Confirmation

This guide provides comprehensive instructions for loading all Environmental Product Declarations (EPDs) from the EC3 API into your vector store, with detailed tracking and confirmation of every step.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [System Setup](#system-setup)
4. [Step-by-Step Loading Process](#step-by-step-loading-process)
5. [Understanding the Process](#understanding-the-process)
6. [Monitoring and Confirmation](#monitoring-and-confirmation)
7. [Post-Load Verification](#post-load-verification)
8. [Troubleshooting](#troubleshooting)
9. [Performance Optimization](#performance-optimization)

---

## Overview

### What This Process Does

The EPD loading pipeline:

1. **Fetches** all EPD records from EC3 API (90,000+ records)
2. **Parses** EPDs into structured database entities
3. **Chunks** large EPD text into manageable pieces (1,500 chars with 200 char overlap)
4. **Generates embeddings** using sentence-transformers (384-dimensional vectors)
5. **Stores** everything in PostgreSQL with pgvector for semantic search
6. **Tracks** every operation with comprehensive logging

### Architecture Summary

```
EC3 API (90,000+ EPDs)
    ↓
EC3Client (Authentication & Pagination)
    ↓
EC3EPDParser (Parse 40+ fields)
    ↓
CarbonEntity + CarbonEntityVerification + EmissionFactor
    ↓
TextChunker (1,500 chars, 200 overlap)
    ↓
VectorManager (sentence-transformers/all-MiniLM-L6-v2)
    ↓
PostgreSQL + pgvector (384-dim embeddings, HNSW index)
```

---

## Prerequisites

### Required Software

- **PostgreSQL 15+** with pgvector extension
- **Python 3.10+**
- **Docker & Docker Compose** (recommended for easy setup)
- **Git** (for cloning the repository)

### Required Credentials

- **EC3 API Credentials** (choose one):
  - API Key (simple)
  - OAuth2 Client ID + Secret + Username + Password (recommended)
  - OAuth2 Authorization Code

### System Requirements

- **Disk Space**: At least 20 GB free (final database ~10-15 GB)
- **RAM**: 8 GB minimum (16 GB recommended)
- **CPU**: Multi-core recommended (can use GPU for faster embeddings)
- **Network**: Stable internet connection for EC3 API calls

---

## System Setup

### Step 1: Start PostgreSQL Database

#### Option A: Using Docker Compose (Recommended)

```bash
# From the Mothra directory
docker compose up -d postgres

# Verify it's running
docker compose ps
```

#### Option B: Using Local PostgreSQL

```bash
# Start PostgreSQL (varies by OS)
sudo systemctl start postgresql  # Linux
brew services start postgresql   # macOS

# Create database
psql -U postgres -c "CREATE DATABASE mothra;"
psql -U postgres -d mothra -c "CREATE EXTENSION vector;"
```

### Step 2: Configure Environment

Copy and edit the `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://mothra:changeme@localhost:5432/mothra

# EC3 API Credentials (OAuth2 - Recommended)
EC3_OAUTH_CLIENT_ID=your_client_id_here
EC3_OAUTH_CLIENT_SECRET=your_client_secret_here
EC3_OAUTH_USERNAME=your_ec3_username
EC3_OAUTH_PASSWORD=your_ec3_password
EC3_OAUTH_SCOPE=read

# Or use API Key (simpler but limited)
# EC3_API_KEY=your_api_key_here

# Embedding Configuration (defaults are fine)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384
```

### Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download embedding model (first time only)
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

### Step 4: Run Database Migrations

```bash
# Initialize database schema
alembic upgrade head
```

### Step 5: Verify System Readiness

Run the comprehensive verification script:

```bash
python scripts/verify_system_ready.py
```

This checks:
- ✓ Database connectivity
- ✓ pgvector extension
- ✓ Required tables
- ✓ EC3 API credentials
- ✓ Embedding model availability
- ✓ System resources

**You must see "System is ready for EPD loading!" before proceeding.**

---

## Step-by-Step Loading Process

### Option 1: Comprehensive Loading with Full Tracking (Recommended)

This enhanced loader provides extensive logging and confirmation:

```bash
# Load ALL EPDs with comprehensive tracking
python scripts/load_epds_comprehensive.py

# Or test with a limited number first
python scripts/load_epds_comprehensive.py --limit 100

# Skip EPDs already in database (for re-runs)
python scripts/load_epds_comprehensive.py --skip-existing

# Custom batch size (default: 50)
python scripts/load_epds_comprehensive.py --batch-size 25
```

**What you'll see:**

```
================================================================================
COMPREHENSIVE EPD VECTOR STORE LOADER
================================================================================
Configuration:
  Batch size:      50
  Skip existing:   False
  Limit:           All EPDs
  Embedding model: sentence-transformers/all-MiniLM-L6-v2
  Embedding dims:  384
  Chunk size:      1500 chars
  Chunk overlap:   200 chars
================================================================================

================================================================================
STARTING EPD EXTRACTION FROM EC3 API
================================================================================
✓ EC3 credentials validated successfully (oauth2_password)

--- Fetching EPD batch at offset 0 ---
✓ Fetched 100 EPDs in this batch
  Sample 1: Portland Cement CEM I 42.5 N (ID: abc123)
  Sample 2: Ready-Mix Concrete C25/30 (ID: def456)
  Sample 3: Structural Steel S355 (ID: ghi789)
  ... and 97 more in this batch

Progress: [██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░] 15.0% (150/1000) - Fetched 150 EPDs

================================================================================
PROCESSING BATCH 1/20 (50 EPDs)
================================================================================

--- EPD 1/50 in batch 1 ---
Processing: Portland Cement CEM I 42.5 N
  EC3 ID: abc123
  ✓ Parsed in 0.045s
  Category: Cement
  Geography: United States
  GWP Total: 950.5 kg CO2e
  ✓ Entity created (ID: 550e8400-e29b-41d4-a716-446655440000)
  ✓ Verification record created (status: verified)
  ✓ Emission factor created
  Text length: 2450 characters
  ✓ Chunked into 2 pieces
  ✓ Embedding completed in 0.123s

[... continues for all EPDs ...]

✓ Batch 1 committed successfully
  Stats: Fetched: 100, Processed: 50, Inserted: 50, Embedded: 50, Chunks: 35

[... continues through all batches ...]

================================================================================
COMPREHENSIVE EPD LOADING REPORT
================================================================================

OVERALL STATISTICS
------------------
Total EPDs Fetched:          1,000
Total Processed:             1,000
Total Inserted:              1,000
Total Embedded:              1,000
Total Chunks Created:        1,250
Total Skipped:               0
Total Errors:                0

PERFORMANCE METRICS
-------------------
Total Time:                  125.50 seconds (2.09 minutes)
Average Rate:                7.96 EPDs/second
Time per EPD:                0.126 seconds

CHUNKING STATISTICS
-------------------
Entities Chunked:            450
Entities Not Chunked:        550
Total Chunks Created:        1,250
Avg Chunks per Entity:       2.78
Max Chunks (single EPD):     8
Min Chunks (single EPD):     2

EMBEDDING STATISTICS
--------------------
Embeddings Generated:        1,000
Embedding Dimensions:        384
Avg Embedding Time:          98.50 ms
Total Embedding Time:        98.50 seconds

CATEGORY BREAKDOWN
------------------
  Concrete                      : 350 (35.0%)
  Steel                         : 200 (20.0%)
  Insulation                    : 150 (15.0%)
  [... etc ...]

GEOGRAPHY BREAKDOWN
-------------------
  United States                 : 400 (40.0%)
  Europe                        : 300 (30.0%)
  Canada                        : 150 (15.0%)
  [... etc ...]

OUTPUT FILES
------------
Detailed Log:     logs/epd_loading_detailed_20250127_143022.log
Summary Log:      logs/epd_loading_summary_20250127_143022.log
EPD Details:      logs/epd_details_20250127_143022.jsonl

================================================================================
```

### Option 2: Standard Loading (Original Script)

The original loader is faster but has less detailed logging:

```bash
# Load all EPDs
python scripts/load_epds_to_vector_store.py

# Or test with limited number
python scripts/load_epds_to_vector_store.py --limit 100
```

---

## Understanding the Process

### Phase 1: Fetching from EC3 API

**What happens:**
- Authenticates with EC3 API (OAuth2 or API Key)
- Fetches EPDs in batches of 100 using pagination
- Continues until all EPDs retrieved or limit reached

**Duration:** ~5-10 minutes for all 90,000 EPDs

**Logging:**
```
✓ EC3 credentials validated successfully (oauth2_password)
Fetching EPDs at offset 0...
✓ Fetched 100 EPDs (total: 100)
Fetching EPDs at offset 100...
✓ Fetched 100 EPDs (total: 200)
[...]
```

### Phase 2: Parsing EPDs

**What happens:**
- EC3EPDParser extracts 40+ fields from each EPD
- Creates CarbonEntity record (main EPD data)
- Creates CarbonEntityVerification record (GWP, LCA stages, etc.)
- Creates EmissionFactor record (if GWP data available)

**Duration:** ~50-100ms per EPD

**Fields Extracted:**
- Basic info: name, description, category
- Geography and temporal scope
- GWP values (total, CO2, CH4, N2O, biogenic, fossil)
- LCA stages (A1-A3, A4-A5, B1-B7, C1-C4, D)
- Environmental indicators (acidification, eutrophication, etc.)
- Verification status and dates
- Material composition
- Quality scores

### Phase 3: Text Chunking

**What happens:**
- Combines EPD fields into searchable text
- If text > 1,500 chars, splits into overlapping chunks
- Each chunk: 1,500 chars with 200 char overlap
- Preserves sentence boundaries where possible

**Why chunk?**
- Embedding models have token limits (~512 tokens)
- Chunks enable finding relevant sections within large EPDs
- Overlaps prevent information loss at boundaries

**Example:**
```
Original EPD: 4,500 characters
→ Chunk 1: chars 0-1,500
→ Chunk 2: chars 1,300-2,800 (200 char overlap with Chunk 1)
→ Chunk 3: chars 2,600-4,100 (200 char overlap with Chunk 2)
```

### Phase 4: Embedding Generation

**What happens:**
- sentence-transformers model encodes text to 384-dim vector
- Each entity gets one embedding (full text or summary)
- Each chunk gets its own embedding
- Embeddings stored in PostgreSQL with pgvector

**Model:** sentence-transformers/all-MiniLM-L6-v2
- Local (no API calls/costs)
- Fast (~100ms per embedding on CPU)
- Good balance of speed and quality
- 384 dimensions (compact but effective)

**Duration:** ~100-150ms per embedding

### Phase 5: Database Storage

**What happens:**
- Entities, verifications, and emission factors stored in PostgreSQL
- Document chunks stored with links to parent entities
- Embeddings stored as pgvector vectors
- HNSW index created for fast similarity search

**Database Tables:**
- `carbon_entities`: Main EPD records
- `carbon_entity_verification`: Detailed verification data
- `emission_factors`: GWP and emission data
- `document_chunks`: Text chunks with embeddings
- `data_sources`: EC3 source metadata

---

## Monitoring and Confirmation

### Real-Time Monitoring

While the loader runs, you can monitor progress in several ways:

#### 1. Console Output

Watch the live console output showing:
- Current batch being processed
- Individual EPD details
- Progress bars with percentages
- Statistics after each batch

#### 2. Log Files

Three log files are created in the `logs/` directory:

**Detailed Log** (`epd_loading_detailed_TIMESTAMP.log`):
```bash
# Watch in real-time
tail -f logs/epd_loading_detailed_*.log
```
Contains every operation, including individual EPD processing.

**Summary Log** (`epd_loading_summary_TIMESTAMP.log`):
```bash
# Watch in real-time
tail -f logs/epd_loading_summary_*.log
```
Contains only major milestones and batch completions.

**EPD Details JSON** (`epd_details_TIMESTAMP.jsonl`):
```bash
# Count loaded EPDs
wc -l logs/epd_details_*.jsonl

# View last 10 EPDs loaded
tail -10 logs/epd_details_*.jsonl | jq .
```
One JSON object per line with EPD metadata.

#### 3. Database Queries

In another terminal, monitor database directly:

```bash
# Connect to database
psql -U mothra -d mothra

# Count EPDs
SELECT COUNT(*) FROM carbon_entities;

# Count embeddings
SELECT COUNT(*) FROM carbon_entities WHERE embedding IS NOT NULL;

# Count chunks
SELECT COUNT(*) FROM document_chunks;

# Recent EPDs
SELECT name, created_at FROM carbon_entities ORDER BY created_at DESC LIMIT 10;
```

### Confirmation Points

The loader provides confirmation at multiple levels:

#### ✓ Per-EPD Confirmation

```
--- EPD 25/50 in batch 3 ---
Processing: Ready-Mix Concrete C30/37
  EC3 ID: xyz789
  ✓ Parsed in 0.042s
  Category: Concrete
  Geography: Germany
  GWP Total: 285.3 kg CO2e
  ✓ Entity created (ID: ...)
  ✓ Verification record created (status: verified)
  ✓ Emission factor created
  Text length: 1,850 characters
  ✓ Chunked into 2 pieces
  ✓ Embedding completed in 0.115s
```

#### ✓ Per-Batch Confirmation

```
✓ Batch 3 committed successfully
  Stats: Fetched: 150, Processed: 150, Inserted: 150, Embedded: 150, Chunks: 95
```

#### ✓ Progress Updates

```
Progress: [████████████████████████░░░░░░░░░░] 60.0% (600/1000) - Batch 12/20 complete
```

#### ✓ Final Report

Comprehensive report with:
- Total counts
- Performance metrics
- Category/geography breakdowns
- Chunking statistics
- Embedding statistics
- Error details (if any)

---

## Post-Load Verification

After loading completes, verify everything worked correctly:

### Step 1: Run Summary Report

```bash
python scripts/epd_summary_report.py
```

This generates a comprehensive report showing:

```
================================================================================
EPD VECTOR STORE SUMMARY REPORT
================================================================================

OVERALL STATISTICS
------------------
Total EPDs in Database:          90,125
Verified Records:                90,125
Emission Factors:                87,450
Total Document Chunks:           125,680

EMBEDDING COVERAGE
------------------
Entities with Embeddings:        90,125 (100.0%)
Chunks with Embeddings:          125,680
Total Embeddings:                215,805

QUALITY METRICS
---------------
Average Quality Score:           0.782
Min Quality Score:               0.500
Max Quality Score:               1.000

GWP STATISTICS
--------------
EPDs with GWP Data:              87,450
Average GWP:                     425.50 kg CO2e
Min GWP:                         1.20 kg CO2e
Max GWP:                         8,950.00 kg CO2e

CHUNKING STATISTICS
-------------------
Entities with Chunks:            45,230
Entities without Chunks:         44,895
Average Chunks per Entity:       2.78
Max Chunks (single EPD):         12
Total Chunks Created:            125,680

[... detailed breakdowns by category, geography, etc. ...]

VECTOR STORE HEALTH
================================================================================
Embedding Coverage:              100.0%
Chunking Rate:                   50.2%
Average Quality:                 0.782/1.0

RECOMMENDATIONS:
  ✓ Excellent embedding coverage.
  ✓ Good average quality score.
  ✓ Good GWP data coverage.

================================================================================
```

Save report to file:
```bash
python scripts/epd_summary_report.py --output-file report.txt
```

Export as JSON:
```bash
python scripts/epd_summary_report.py --format json --output-file report.json
```

### Step 2: Test Semantic Search

Verify embeddings work correctly:

```bash
python scripts/query_epd_vector_store.py "low carbon concrete"
```

Expected output:
```
Top 10 Results for: "low carbon concrete"

1. Low-Carbon Concrete Mix C25/30 (similarity: 0.92)
   Category: Concrete
   GWP: 185.5 kg CO2e

2. Portland Limestone Cement Concrete (similarity: 0.89)
   Category: Concrete
   GWP: 210.3 kg CO2e

[... etc ...]
```

### Step 3: Verify Database State

```sql
-- Connect to database
psql -U mothra -d mothra

-- Check counts
SELECT
    (SELECT COUNT(*) FROM carbon_entities) as total_epds,
    (SELECT COUNT(*) FROM carbon_entities WHERE embedding IS NOT NULL) as with_embeddings,
    (SELECT COUNT(*) FROM document_chunks) as total_chunks,
    (SELECT COUNT(*) FROM carbon_entity_verification) as verified_records;

-- Check category distribution
SELECT
    category_hierarchy[1] as category,
    COUNT(*) as count
FROM carbon_entities
GROUP BY category_hierarchy[1]
ORDER BY count DESC
LIMIT 10;

-- Check recent additions
SELECT
    name,
    created_at,
    quality_score
FROM carbon_entities
ORDER BY created_at DESC
LIMIT 10;

-- Verify vector index
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'carbon_entities'
    AND indexname LIKE '%embedding%';
```

---

## Troubleshooting

### Issue: Database Connection Failed

**Symptom:**
```
✗ Database connection [FAIL]
  → Error: [Errno 111] Connect call failed
```

**Solutions:**
1. Start PostgreSQL: `docker compose up -d postgres`
2. Check connection string in `.env`
3. Verify PostgreSQL is running: `docker compose ps`
4. Check firewall/network settings

### Issue: EC3 API Authentication Failed

**Symptom:**
```
✗ EC3 API credentials are invalid
  → Auth method: oauth2_password
```

**Solutions:**
1. Verify credentials in `.env` file
2. Check for typos in client ID/secret
3. Try using API key instead: `EC3_API_KEY=your_key`
4. Test credentials manually: `python scripts/test_ec3_connection.py`
5. Request new credentials from Building Transparency

### Issue: pgvector Extension Missing

**Symptom:**
```
✗ pgvector extension [FAIL]
  → pgvector NOT installed
```

**Solutions:**
1. Install pgvector in PostgreSQL:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
2. Or run migrations: `alembic upgrade head`
3. Verify installation: `SELECT * FROM pg_extension WHERE extname='vector';`

### Issue: Embedding Model Download Fails

**Symptom:**
```
✗ Embedding model [FAIL]
  → Error loading model: Connection timeout
```

**Solutions:**
1. Check internet connection
2. Manually download model:
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
   ```
3. Set proxy if needed: `export HTTPS_PROXY=http://proxy:port`
4. Use cached model if previously downloaded

### Issue: Out of Memory During Loading

**Symptom:**
```
MemoryError: Unable to allocate array
```

**Solutions:**
1. Reduce batch size: `--batch-size 10`
2. Close other applications
3. Increase system RAM or swap space
4. Process in smaller chunks: `--limit 1000` multiple times with `--skip-existing`

### Issue: Slow Performance

**Symptom:**
Processing rate < 2 EPDs/second

**Solutions:**
1. Check CPU usage: embeddings are CPU-intensive
2. Use GPU if available (CUDA)
3. Reduce batch size to avoid memory swapping
4. Check network latency to EC3 API
5. Verify database isn't disk-bound
6. Disable unnecessary logging: `--log-level WARNING`

### Issue: Some EPDs Failed to Process

**Symptom:**
```
Total Errors: 25
```

**Review error details:**
1. Check detailed log for error messages
2. Review error section in final report
3. Re-run with `--skip-existing` to process only failed ones

**Common causes:**
- Malformed EPD data from EC3
- Missing required fields
- Database constraint violations
- Network timeouts

---

## Performance Optimization

### For Faster Loading

1. **Use GPU for Embeddings:**
   ```bash
   # Verify CUDA available
   python -c "import torch; print(torch.cuda.is_available())"
   ```
   GPU can be 5-10x faster than CPU.

2. **Increase Batch Size:**
   ```bash
   python scripts/load_epds_comprehensive.py --batch-size 100
   ```
   Larger batches = fewer commits, but more memory.

3. **Disable Detailed Logging:**
   ```bash
   python scripts/load_epds_comprehensive.py --log-level WARNING
   ```
   Less I/O = faster processing.

4. **Use SSD for Database:**
   PostgreSQL performance heavily depends on disk speed.

5. **Tune PostgreSQL:**
   ```sql
   -- Increase shared buffers
   ALTER SYSTEM SET shared_buffers = '4GB';

   -- Increase work mem
   ALTER SYSTEM SET work_mem = '256MB';

   -- Reload config
   SELECT pg_reload_conf();
   ```

### For Lower Resource Usage

1. **Reduce Batch Size:**
   ```bash
   python scripts/load_epds_comprehensive.py --batch-size 10
   ```

2. **Process in Chunks:**
   ```bash
   # Load 10,000 at a time
   python scripts/load_epds_comprehensive.py --limit 10000
   python scripts/load_epds_comprehensive.py --limit 10000 --skip-existing
   [repeat...]
   ```

3. **Use Smaller Embedding Model:**
   Edit `.env`:
   ```bash
   EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L3-v2
   EMBEDDING_DIMENSION=384
   ```
   (Faster but potentially lower quality)

---

## Summary Checklist

Before loading EPDs:
- [ ] PostgreSQL running and accessible
- [ ] pgvector extension installed
- [ ] Database schema migrated (`alembic upgrade head`)
- [ ] EC3 API credentials configured in `.env`
- [ ] Python dependencies installed
- [ ] Embedding model downloaded
- [ ] System verification passed (`python scripts/verify_system_ready.py`)

During loading:
- [ ] Monitor console output for errors
- [ ] Watch log files for detailed progress
- [ ] Check database periodically for record counts
- [ ] Verify sufficient disk space remains

After loading:
- [ ] Run summary report (`python scripts/epd_summary_report.py`)
- [ ] Test semantic search functionality
- [ ] Verify embedding coverage is ~100%
- [ ] Check for any errors in final report
- [ ] Backup database if desired

---

## Additional Resources

### Scripts Reference

| Script | Purpose |
|--------|---------|
| `verify_system_ready.py` | Check if system is ready for loading |
| `load_epds_comprehensive.py` | Enhanced loader with full tracking |
| `load_epds_to_vector_store.py` | Standard loader (faster, less logging) |
| `epd_summary_report.py` | Generate post-load summary report |
| `query_epd_vector_store.py` | Test semantic search |

### Documentation

- `EC3_INTEGRATION_GUIDE.md` - EC3 API integration details
- `EC3_AUTHENTICATION_GUIDE.md` - Authentication setup
- `CHUNKING_IMPLEMENTATION.md` - Text chunking strategy
- `QUICKSTART.md` - Quick start guide

### Support

For issues or questions:
1. Check troubleshooting section above
2. Review log files for error details
3. Consult documentation
4. Open GitHub issue with:
   - Error messages
   - Log file excerpts
   - System configuration
   - Steps to reproduce

---

## Conclusion

Following this guide, you should now have:

✓ All available EPDs loaded from EC3 API
✓ Comprehensive tracking and logs of the process
✓ Text chunking for large EPDs
✓ 384-dimensional embeddings for semantic search
✓ Full verification and confirmation of data
✓ Detailed reports on what was loaded

Your vector store is now ready for semantic search, carbon analysis, and EPD discovery!

**Next Steps:**
- Explore EPDs via semantic search
- Build applications using the vector store
- Set up automated updates to keep data fresh
- Integrate with other carbon data sources

---

*Last Updated: 2025-01-27*
