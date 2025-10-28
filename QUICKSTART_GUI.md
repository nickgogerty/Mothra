# MOTHRA GUI Quick Start Guide

Get the beautiful Swiss-minimal interface running in minutes!

## Prerequisites

Make sure you have:
- ✅ Python 3.11+ installed
- ✅ Node.js 18+ installed
- ✅ PostgreSQL running with MOTHRA database
- ✅ pgvector extension installed

## Step 1: Install Dependencies

### Backend (Python)
```bash
# Install required packages
pip install fastapi uvicorn sqlalchemy asyncpg psycopg2-binary pydantic python-dotenv
```

### Frontend (Node.js)
```bash
cd frontend
npm install
cd ..
```

## Step 2: Configure Environment

Create `.env` file in project root (if not already):
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/mothra
EMBEDDING_DIMENSION=384
```

Create `frontend/.env`:
```bash
cp frontend/.env.example frontend/.env
```

## Step 3: Start the Backend

Open a terminal and run:
```bash
python run_api.py
```

You should see:
```
Starting MOTHRA API server...
API will be available at: http://localhost:8000
API documentation at: http://localhost:8000/api/docs
```

## Step 4: Start the Frontend

Open a **new terminal** and run:
```bash
cd frontend
npm run dev
```

You should see:
```
VITE v5.1.3  ready in 500 ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

## Step 5: Open Your Browser

Navigate to: **http://localhost:3000**

You should see the MOTHRA dashboard with:
- Total entities count
- Data sources count
- Quality distribution charts
- Entity type breakdown

## Using the Interface

### Dashboard (Home)
- Overview of database statistics
- Quality distribution visualization
- Entity type breakdown with validation status
- GHG scope coverage

### Search
- Enter natural language queries
- Filter by entity type
- See similarity scores
- Click results to view details

### Entities
- Browse all carbon entities
- Filter by type, validation, quality
- Sort and paginate results
- Click any row to view full details

### Sources
- Monitor all data sources
- View crawl history and status
- Check error counts
- See update frequencies

## Troubleshooting

### Backend won't start
```bash
# Check if database is running
psql -U postgres -c "SELECT 1"

# Verify database URL
echo $DATABASE_URL

# Check if port 8000 is available
lsof -i :8000
```

### Frontend won't start
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node version
node --version  # Should be 18+
```

### Cannot connect to API
1. Verify backend is running on port 8000
2. Check `frontend/.env` has correct API URL
3. Look for CORS errors in browser console

### No data showing
1. Ensure database has data (run ingestion scripts)
2. Check backend logs for errors
3. Open browser DevTools → Network tab to see API responses

## API Documentation

Once backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

Try out the API endpoints directly from the browser!

## What's Next?

### Explore Features
- Try semantic search with queries like "concrete emissions"
- Filter entities by quality score
- Monitor data source health
- View detailed emission factors

### Customize
- Edit `frontend/src/theme.js` to adjust colors
- Modify `frontend/src/components/` to add features
- Update `mothra/api/routes/` to add endpoints

### Deploy
See `GUI_README.md` for production deployment instructions.

## Getting Help

Check these resources:
- **Full Documentation**: See `GUI_README.md`
- **Frontend README**: See `frontend/README.md`
- **API Docs**: http://localhost:8000/api/docs
- **Main MOTHRA Docs**: See `MOTHRA_SUMMARY.md`

## Design Philosophy

This interface follows:
- **Tufte**: High data-ink ratio, minimal chartjunk
- **Nielsen**: Usability, clear feedback, user control
- **Swiss Design**: Grid-based, minimal, clean typography

Enjoy exploring your carbon data! 🌍📊
