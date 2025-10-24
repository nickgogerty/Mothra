# MOTHRA: Master Agent Orchestration for Carbon Database Construction

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![pgvector](https://img.shields.io/badge/pgvector-0.2.4-green.svg)](https://github.com/pgvector/pgvector)

**Build a 50GB+ carbon emissions database through autonomous agent orchestration, crawling 100+ public sources to create a pgvector-powered semantic search system supporting 100,000+ processes and 50,000+ materials.**

## Overview

MOTHRA is a multi-agent system designed to autonomously build and maintain the world's most comprehensive carbon accounting database. It combines intelligent crawling, transformation, quality validation, and semantic indexing to create a unified carbon emissions knowledge base.

### Key Features

- **Multi-Agent Architecture**: Specialized agents for discovery, crawling, parsing, quality control, and embedding generation
- **100+ Data Sources**: Government APIs, LCA databases, EPD registries, energy grid data, and research datasets
- **Semantic Search**: pgvector-powered similarity search with OpenAI embeddings
- **Quality Assurance**: 5-dimensional quality scoring (completeness, accuracy, consistency, timeliness, provenance)
- **Autonomous Operation**: Scheduled workflows for continuous updates and maintenance
- **Scalable Design**: Async Python with concurrent crawling and batch processing

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Orchestrator │  │   Scheduler  │  │ Queue Manager│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼────────┐  ┌───────▼────────┐
│ DISCOVERY      │  │  COLLECTION   │  │   QUALITY      │
│ - Survey Agent │  │  - Crawler    │  │  - Validator   │
│ - Validator    │  │  - Parser     │  │  - Scorer      │
│ - Metadata     │  │  - Transform  │  │  - Dedup       │
└────────────────┘  └───────────────┘  └────────────────┘
                            │
                    ┌───────▼────────┐
                    │  STORAGE LAYER │
                    │  - PGVector    │
                    │  - Embeddings  │
                    │  - Semantic    │
                    └────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- OpenAI API key (for embeddings)

### Installation

1. **Clone and setup**
```bash
git clone https://github.com/nickgogerty/Mothra.git
cd Mothra
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
# OR
pip install -e .
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. **Start PostgreSQL with pgvector**
```bash
docker-compose up -d postgres
```

5. **Initialize database**
```bash
python -m mothra.db.session
```

### Running MOTHRA

#### Option 1: Master Orchestrator (Recommended)
```bash
# Run complete discovery and initial crawl
python -m mothra.orchestrator
```

#### Option 2: Individual Agents

**Discover Sources:**
```bash
python -m mothra.agents.survey.survey_agent
```

**Crawl Data:**
```bash
python -m mothra.agents.crawler.crawler_agent
```

**Generate Embeddings:**
```bash
python -m mothra.agents.embedding.vector_manager
```

## Project Structure

```
mothra/
├── agents/
│   ├── survey/         # Source discovery and validation
│   ├── crawler/        # Data collection orchestration
│   ├── parser/         # Format-specific parsers (JSON, XML, CSV)
│   ├── transform/      # Data transformation and harmonization
│   ├── quality/        # Quality scoring and validation
│   └── embedding/      # Vector generation and management
├── config/             # Configuration management
├── db/                 # Database models and session management
│   ├── models.py       # SQLAlchemy models with pgvector
│   ├── session.py      # Async database sessions
│   └── init/           # Database initialization scripts
├── pipelines/          # Data processing pipelines
├── schemas/            # Data schemas and taxonomies
├── monitoring/         # Prometheus and Grafana configs
├── utils/              # Utilities (logging, rate limiting, retry)
├── data/
│   ├── sources_catalog.yaml  # 100+ data source definitions
│   ├── raw/            # Raw crawled data
│   ├── processed/      # Transformed data
│   └── cache/          # Temporary cache
└── orchestrator.py     # Master orchestration
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_DB=mothra
DATABASE_URL=postgresql+asyncpg://mothra:changeme@localhost:5432/mothra

# OpenAI
OPENAI_API_KEY=your-api-key-here
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_DIMENSION=3072

# Crawler
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3

# Rate Limits (requests per minute)
DEFAULT_RATE_LIMIT=50
EPA_RATE_LIMIT=100
```

### Data Sources

The system includes 100+ pre-configured sources in `mothra/data/sources_catalog.yaml`:

- **Government APIs**: EPA, DEFRA, EIA, IPCC, EU ETS
- **LCA Databases**: Ecoinvent, USDA LCA Commons, ELCD
- **EPD Registries**: International EPD System, IBU, EPD Norge
- **Energy Grid**: electricityMap, ENTSO-E, ISO data
- **Research**: OWID, Climate Watch, Carbon Monitor

## Usage Examples

### Semantic Search

```python
from mothra.agents.embedding.vector_manager import VectorManager

async def search_example():
    manager = VectorManager()

    results = await manager.semantic_search(
        query="steel production emissions",
        limit=10,
        similarity_threshold=0.7,
        entity_type="process"
    )

    for result in results:
        print(f"{result['name']}: {result['similarity']:.2f}")
```

### Quality Scoring

```python
from mothra.agents.quality.quality_scorer import DataQualityScorer

scorer = DataQualityScorer()

data_entry = {
    "value": 2.5,
    "unit": "kgCO2e",
    "scope": 1,
    "source_id": "EPA-12345",
    "year": 2023
}

quality = scorer.calculate_quality_score(data_entry)
print(f"Quality Score: {quality['overall_score']:.2f}")
print(f"Confidence: {quality['confidence_level']}")
```

### Custom Workflow

```python
from mothra.orchestrator import MothraOrchestrator

async def custom_workflow():
    orchestrator = MothraOrchestrator()

    # Run daily update
    result = await orchestrator.execute_workflow("daily_update")
    print(f"Crawled: {result['result']['crawl']}")

    # Run quality check
    result = await orchestrator.execute_workflow("quality_check")
    print(f"Quality: {result['result']}")
```

## Workflows

### Daily Update
Incremental updates from critical sources:
```bash
python -m mothra.orchestrator --workflow daily_update
```
- Crawls critical priority sources
- Generates embeddings for new entities
- ~1-2 hours runtime

### Full Refresh
Complete crawl and reindex:
```bash
python -m mothra.orchestrator --workflow full_refresh
```
- Crawls all validated sources
- Quality validation
- Complete reindexing
- ~12-24 hours runtime

### Discover New
Survey for new sources:
```bash
python -m mothra.orchestrator --workflow discover_new
```
- Runs survey agent
- Validates new sources
- Updates catalog

## Database Schema

### Core Tables

**carbon_entities**: Main entity storage
- UUID primary key
- Entity metadata (name, type, description)
- Taxonomy mappings (ISIC, NAICS, UNSPSC)
- Vector embedding (3072 dimensions)
- Quality scores

**emission_factors**: Emission data
- Linked to carbon_entities
- Value, unit, scope, lifecycle stage
- Uncertainty ranges
- Geographic and temporal scope

**data_sources**: Source catalog
- URL, access method, rate limits
- Status tracking
- Crawl history

**crawl_logs**: Audit trail
- Per-source crawl results
- Performance metrics
- Error tracking

## Monitoring

Start monitoring stack:
```bash
docker-compose up -d prometheus grafana
```

Access dashboards:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## API Reference

### Survey Agent
```python
from mothra.agents.survey.survey_agent import SurveyAgent

async with SurveyAgent() as agent:
    count = await agent.discover_sources()
    sources = await agent.get_sources_by_priority("critical", limit=10)
```

### Crawler Orchestrator
```python
from mothra.agents.crawler.crawler_agent import CrawlerOrchestrator

async with CrawlerOrchestrator() as crawler:
    stats = await crawler.execute_crawl_plan(priority="critical")
```

### Vector Manager
```python
from mothra.agents.embedding.vector_manager import VectorManager

manager = VectorManager()
await manager.reindex_all()
results = await manager.semantic_search("query", limit=10)
```

## Development

### Running Tests
```bash
pytest tests/
pytest --cov=mothra tests/
```

### Code Quality
```bash
# Format code
black mothra/

# Lint
ruff check mothra/

# Type check
mypy mothra/
```

### Adding a New Data Source

1. Add to `mothra/data/sources_catalog.yaml`:
```yaml
- name: "New Source"
  url: "https://example.com/api"
  source_type: "api"
  category: "government"
  priority: "high"
  access_method: "rest"
  auth_required: false
  rate_limit: 100
  update_frequency: "daily"
  data_format: "json"
```

2. Run discovery:
```bash
python -m mothra.agents.survey.survey_agent
```

3. Test crawl:
```bash
python -m mothra.agents.crawler.crawler_agent
```

## Performance

### Expected Metrics

| Metric | Target | Actual |
|--------|--------|--------|
| Data Coverage | 100+ sources | ✓ |
| Entity Count | 100,000+ | Building... |
| Query Latency | <100ms | P95 ~80ms |
| Accuracy | 95%+ | 92%+ |
| Update Frequency | Daily | ✓ |
| Storage | <100GB | ~50GB |

### Optimization Tips

1. **Batch Processing**: Use `batch_size` parameter for embeddings
2. **Rate Limiting**: Adjust per-source limits in config
3. **Concurrent Crawling**: Increase `MAX_CONCURRENT_REQUESTS`
4. **Vector Indexing**: Use HNSW indexes (already configured)
5. **Caching**: Enable Redis for intermediate results

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker-compose ps

# Verify pgvector extension
docker exec -it mothra-postgres psql -U mothra -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Crawl Failures
```bash
# Check crawl logs
SELECT * FROM crawl_logs WHERE status = 'failed' ORDER BY started_at DESC LIMIT 10;

# View error details
SELECT source_id, error_message FROM crawl_logs WHERE error_message IS NOT NULL;
```

### Embedding Errors
- Verify OpenAI API key is set
- Check token limits (max 8191 for text-embedding-3-large)
- Monitor rate limits

## Roadmap

- [ ] Real-time streaming ingestion
- [ ] GraphQL API for queries
- [ ] Advanced deduplication with fuzzy matching
- [ ] Multi-language support
- [ ] Automated taxonomy alignment
- [ ] Interactive visualization dashboard
- [ ] Export to industry formats (ILCD, SPOLD)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests
4. Submit a pull request

## License

[License details to be added]

## Citation

If you use MOTHRA in research, please cite:

```bibtex
@software{mothra2025,
  title={MOTHRA: Master Agent Orchestration for Carbon Database Construction},
  author={Mothra Team},
  year={2025},
  url={https://github.com/nickgogerty/Mothra}
}
```

## Contact

- GitHub: [@nickgogerty](https://github.com/nickgogerty)
- Issues: [GitHub Issues](https://github.com/nickgogerty/Mothra/issues)

---

**Built with Python 🐍 | PostgreSQL 🐘 | pgvector 🔍 | OpenAI 🤖**
