# Quick Start Guide - Testing MOTHRA Search

Follow these steps to install the package and test semantic search:

## Step 1: Install the MOTHRA package

From your `Mothra` directory with your virtual environment activated:

```bash
pip install -e .
```

This installs the `mothra` package in development mode, making all imports work.

## Step 2: Verify Installation

```bash
python -c "from mothra.db.models import CarbonEntity; print('✅ Import successful!')"
```

You should see `✅ Import successful!`

## Step 3: Add Sample Data

```bash
python scripts/add_sample_data.py
```

This will add 20 sample carbon entities to your database.

## Step 4: Generate Embeddings

```bash
python -m mothra.agents.embedding.vector_manager
```

This generates vector embeddings for all entities (needed for semantic search).

## Step 5: Test Semantic Search

```bash
python scripts/test_search.py
```

This will:
- Run sample queries automatically
- Drop you into interactive mode where you can type your own queries

## Sample Queries to Try

Once in interactive mode, try these:

- `steel production emissions`
- `renewable electricity`
- `transportation by truck`
- `concrete and cement`
- `livestock and agriculture`
- `plastic materials`
- `waste management`

## Troubleshooting

**Error: `No module named 'mothra'`**
- Make sure you ran `pip install -e .` from the Mothra directory
- Verify your virtual environment is activated: `which python` should show the venv path

**Error: Database connection failed**
- Make sure Docker containers are running: `docker compose ps`
- If not running: `docker compose up -d`

**Error: No results found**
- Make sure you ran step 3 (add sample data)
- Make sure you ran step 4 (generate embeddings)

## Expected Output

After step 3, you should see:
```
✅ Added 20 sample carbon entities!
```

After step 4, you should see embeddings being generated:
```
reindexing_started total_entities=20
batch_embedded total=20 successful=20
reindex_complete total=20 reindexed=20
```

After step 5, you should see search results with similarity scores like:
```
🔍 Query: 'steel production emissions'

Found 2 results:

1. Steel production from blast furnace
   Type: process
   Similarity: 0.752 (75.2%)
   Quality: 0.90
   ...
```
