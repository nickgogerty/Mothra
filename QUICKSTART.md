# MOTHRA Quick Start Guide

Get MOTHRA up and running in 5 minutes.

## Prerequisites Check

```bash
# Check Python version (need 3.11+)
python --version

# Check Docker
docker --version
docker-compose --version

# Check you have an OpenAI API key
```

## Step-by-Step Setup

### 1. Clone and Install

```bash
# Clone repository
git clone https://github.com/nickgogerty/Mothra.git
cd Mothra

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set your OpenAI API key
nano .env  # or use your favorite editor
```

**Required configuration:**
```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Start Database

```bash
# Start PostgreSQL with pgvector
docker-compose up -d postgres

# Wait for database to be ready (about 10 seconds)
sleep 10

# Verify it's running
docker-compose ps
```

### 4. Initialize Database

```python
# Run Python initialization
python -c "
import asyncio
from mothra.db.session import init_db
asyncio.run(init_db())
print('Database initialized!')
"
```

### 5. Run First Workflow

```bash
# Discover and catalog sources
python -m mothra.agents.survey.survey_agent
```

This will:
- Load the 100+ source catalog
- Validate source accessibility
- Populate the data_sources table
- Take ~2-5 minutes

### 6. Start Crawling (Optional)

```bash
# Crawl critical priority sources
python -m mothra.agents.crawler.crawler_agent
```

**Note:** This will actually fetch data from live APIs. Start with a small test first.

## Verify Installation

```python
# Test database connection
python -c "
import asyncio
from mothra.db.session import get_db_context
from sqlalchemy import text

async def test():
    async with get_db_context() as db:
        result = await db.execute(text('SELECT version()'))
        print(result.scalar())
        result = await db.execute(text(\"SELECT extversion FROM pg_extension WHERE extname='vector'\"))
        print(f'pgvector version: {result.scalar()}')

asyncio.run(test())
"
```

Expected output:
```
PostgreSQL 15.x...
pgvector version: 0.5.x
```

## Next Steps

### Option A: Run Full Orchestrator
```bash
python -m mothra.orchestrator
```

### Option B: Individual Components

**Discover sources:**
```bash
python -m mothra.agents.survey.survey_agent
```

**Crawl data:**
```bash
python -m mothra.agents.crawler.crawler_agent
```

**Generate embeddings:**
```bash
python -m mothra.agents.embedding.vector_manager
```

## Common Issues

### Issue: Docker not starting
**Solution:**
```bash
# Check Docker daemon is running
docker info

# Restart Docker service
# On Mac: Restart Docker Desktop
# On Linux:
sudo systemctl restart docker
```

### Issue: Database connection refused
**Solution:**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check logs
docker-compose logs postgres

# Restart if needed
docker-compose restart postgres
```

### Issue: OpenAI API errors
**Solution:**
- Verify API key is correct in `.env`
- Check API key has credits
- Verify no rate limiting

### Issue: Module not found
**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

## Development Mode

For development with auto-reload:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black mothra/

# Run tests
pytest tests/
```

## Monitoring

Start monitoring stack:

```bash
# Start Prometheus and Grafana
docker-compose up -d prometheus grafana

# Access dashboards
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana (admin/admin)
```

## Success Criteria

After setup, you should have:
- ✅ PostgreSQL running with pgvector extension
- ✅ Data sources cataloged in database
- ✅ No errors in logs
- ✅ Able to run survey agent successfully

Check database:
```sql
-- Connect to database
docker exec -it mothra-postgres psql -U mothra

-- Check sources
SELECT count(*) FROM data_sources;
SELECT name, status, priority FROM data_sources LIMIT 10;
```

## What's Next?

1. **Customize sources**: Edit `mothra/data/sources_catalog.yaml`
2. **Configure crawling**: Adjust rate limits in `.env`
3. **Set up scheduling**: Configure cron jobs for workflows
4. **Add monitoring**: Set up alerts in Grafana
5. **Explore data**: Query the semantic search API

## Getting Help

- **Documentation**: See [README.md](README.md)
- **Issues**: [GitHub Issues](https://github.com/nickgogerty/Mothra/issues)
- **Logs**: Check `mothra/*.log` files

## Clean Restart

If you need to start fresh:

```bash
# Stop all services
docker-compose down -v

# Remove data
rm -rf mothra/data/raw/* mothra/data/processed/*

# Restart
docker-compose up -d postgres
# Then repeat initialization steps
```

---

**You're ready to build the carbon database!** 🚀
