# MOTHRA Installation Guide

## Quick Start (5 Minutes)

### For Mac/Linux:
```bash
git clone https://github.com/nickgogerty/Mothra.git
cd Mothra
git checkout claude/mothra-carbon-database-011CUSGHTrH9htbUpPmK5pdM
bash setup.sh
```

### For Windows:
```cmd
git clone https://github.com/nickgogerty/Mothra.git
cd Mothra
git checkout claude/mothra-carbon-database-011CUSGHTrH9htbUpPmK5pdM
setup.bat
```

That's it! The script handles everything automatically.

## What the Setup Script Does

The automated setup script (`setup.sh` for Mac/Linux, `setup.bat` for Windows) performs all these steps:

1. ✅ **Checks prerequisites** (Python 3.11+, Docker)
2. ✅ **Creates virtual environment** (`venv/`)
3. ✅ **Installs all dependencies** (including sentence-transformers)
4. ✅ **Creates .env file** (no API keys needed!)
5. ✅ **Starts PostgreSQL with pgvector** in Docker
6. ✅ **Initializes database schema** with vector extension
7. ✅ **Discovers 100+ data sources** and catalogs them
8. ✅ **Tests embeddings** to ensure everything works

## Prerequisites

Before running the setup script, make sure you have:

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/downloads)
- **4GB free RAM** (for PostgreSQL + sentence-transformers)
- **5GB free disk space** (for models and data)

## After Setup

Once setup completes, you can:

### Start Crawling Critical Sources
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m mothra.agents.crawler.crawler_agent
```

### Run Full Orchestrator
```bash
python -m mothra.orchestrator
```

### Check Database
```bash
# See how many sources were discovered
docker exec -it mothra-postgres psql -U mothra -c "SELECT count(*) FROM data_sources;"

# See sources by priority
docker exec -it mothra-postgres psql -U mothra -c "SELECT name, priority, status FROM data_sources LIMIT 10;"
```

### Test Semantic Search
```python
from mothra.agents.embedding.vector_manager import VectorManager
import asyncio

async def test_search():
    manager = VectorManager()
    results = await manager.semantic_search("steel production emissions", limit=5)
    for result in results:
        print(f"{result['name']}: {result['similarity']:.2f}")

asyncio.run(test_search())
```

## Troubleshooting

### Setup Script Fails

**Issue: Docker not found**
```bash
# Install Docker Desktop, then restart terminal
docker --version
```

**Issue: Python version too old**
```bash
# Check version
python3 --version

# Need 3.11+, upgrade if necessary
```

**Issue: Permission denied on setup.sh**
```bash
chmod +x setup.sh
./setup.sh
```

### Database Connection Issues

**Issue: PostgreSQL not starting**
```bash
# Check Docker is running
docker ps

# View logs
docker compose logs postgres

# Restart
docker compose restart postgres
```

**Issue: Port 5432 already in use**
```bash
# Find what's using the port
lsof -i :5432  # Mac/Linux
netstat -ano | findstr :5432  # Windows

# Stop conflicting service or change MOTHRA's port in docker-compose.yml
```

### Embedding Issues

**Issue: Model download fails**
```bash
# Manually download model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

**Issue: Out of memory**
- Close other applications
- Increase Docker memory limit in Docker Desktop settings
- Use a smaller batch size in config

## Manual Installation (If Script Fails)

If the automated script doesn't work, follow these manual steps:

```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create config
cp .env.example .env

# 4. Start database
docker compose up -d postgres
sleep 10

# 5. Initialize database
python -c "import asyncio; from mothra.db.session import init_db; asyncio.run(init_db())"

# 6. Discover sources
python -m mothra.agents.survey.survey_agent
```

## Verify Installation

Run these commands to verify everything is working:

```bash
# Check database connection
python -c "import asyncio; from mothra.db.session import get_db_context; from sqlalchemy import text; async def test(): async with get_db_context() as db: result = await db.execute(text('SELECT 1')); print('✅ Database OK'); asyncio.run(test())"

# Check pgvector extension
docker exec -it mothra-postgres psql -U mothra -c "SELECT extversion FROM pg_extension WHERE extname='vector';"

# Check sentence-transformers
python -c "from sentence_transformers import SentenceTransformer; print('✅ Embeddings OK')"

# Check data sources
docker exec -it mothra-postgres psql -U mothra -c "SELECT count(*) as source_count FROM data_sources;"
```

Expected output:
- ✅ Database OK
- pgvector version: 0.5.x or higher
- ✅ Embeddings OK
- source_count: 40+ sources

## Configuration

All configuration is in `.env`:

```bash
# Database (already configured)
POSTGRES_HOST=localhost
POSTGRES_DB=mothra

# Embeddings (no API key needed!)
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Crawler settings (adjust as needed)
MAX_CONCURRENT_REQUESTS=10
DEFAULT_RATE_LIMIT=50

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## Next Steps

Once installed:

1. **Explore the data sources**: Check what was discovered
2. **Start crawling**: Begin collecting carbon data
3. **Generate embeddings**: Enable semantic search
4. **Query the database**: Search for carbon entities
5. **Set up workflows**: Automate daily updates

## Getting Help

- **Documentation**: See [README.md](README.md)
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **Issues**: [GitHub Issues](https://github.com/nickgogerty/Mothra/issues)

## Clean Restart

If you need to start over:

```bash
# Stop services
docker compose down -v

# Remove virtual environment
rm -rf venv/

# Remove data
rm -rf mothra/data/raw/* mothra/data/processed/*

# Run setup again
bash setup.sh
```

---

**Ready to build the world's most comprehensive carbon database!** 🦋
