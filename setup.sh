#!/bin/bash
# MOTHRA Setup Script - Automated Installation and Initialization
# Run this script on your local machine: bash setup.sh

set -e  # Exit on error

echo "🦋 MOTHRA Setup Script"
echo "======================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}[1/8] Checking prerequisites...${NC}"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python $PYTHON_VERSION found"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker${NC}"
    exit 1
fi
echo "✅ Docker found"

# Check if docker compose works
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo -e "${RED}❌ Docker Compose not found${NC}"
    exit 1
fi
echo "✅ Docker Compose found"

# Step 2: Create virtual environment
echo ""
echo -e "${BLUE}[2/8] Creating Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Step 3: Install dependencies
echo ""
echo -e "${BLUE}[3/8] Installing Python dependencies...${NC}"
echo "This may take a few minutes (downloading sentence-transformers model)..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "✅ Dependencies installed"

# Step 4: Create .env file
echo ""
echo -e "${BLUE}[4/8] Creating environment configuration...${NC}"
if [ -f ".env" ]; then
    echo ".env already exists, skipping..."
else
    cp .env.example .env
    echo "✅ .env file created"
fi

# Step 5: Start Docker services
echo ""
echo -e "${BLUE}[5/8] Starting PostgreSQL with pgvector...${NC}"
$DOCKER_COMPOSE up -d postgres
echo "Waiting for PostgreSQL to be ready..."
sleep 10

# Verify PostgreSQL is running
if docker ps | grep -q mothra-postgres; then
    echo "✅ PostgreSQL is running"
else
    echo -e "${RED}❌ PostgreSQL failed to start${NC}"
    $DOCKER_COMPOSE logs postgres
    exit 1
fi

# Step 6: Initialize database
echo ""
echo -e "${BLUE}[6/8] Initializing database schema...${NC}"
python3 -c "
import asyncio
from mothra.db.session import init_db
asyncio.run(init_db())
print('✅ Database initialized with pgvector extension')
"

# Step 7: Discover sources
echo ""
echo -e "${BLUE}[7/8] Discovering carbon data sources...${NC}"
python3 -m mothra.agents.survey.survey_agent
echo "✅ Sources discovered and cataloged"

# Step 8: Test embeddings
echo ""
echo -e "${BLUE}[8/8] Testing local embeddings...${NC}"
python3 -c "
from sentence_transformers import SentenceTransformer
import sys
print('Loading sentence-transformers model...')
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
embedding = model.encode('test carbon emissions')
print(f'✅ Embeddings working! Dimension: {len(embedding)}')
"

# Success message
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}🎉 MOTHRA Setup Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Start crawling critical sources:"
echo "   python -m mothra.agents.crawler.crawler_agent"
echo ""
echo "2. Or run the full orchestrator:"
echo "   python -m mothra.orchestrator"
echo ""
echo "3. Check database:"
echo "   docker exec -it mothra-postgres psql -U mothra -c 'SELECT count(*) FROM data_sources;'"
echo ""
echo "4. View logs:"
echo "   docker-compose logs -f postgres"
echo ""
echo "To activate the virtual environment in a new terminal:"
echo "   source venv/bin/activate"
echo ""
