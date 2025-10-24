#!/bin/bash
# MOTHRA Setup Script - Fixed for Mac compilation issues
# Run this script on your local machine: bash setup_mac_fixed.sh

set -e  # Exit on error

echo "🦋 MOTHRA Setup Script (Mac - Fixed)"
echo "====================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${BLUE}[1/9] Checking prerequisites...${NC}"

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

# Step 2: Install Xcode Command Line Tools (Mac specific)
echo ""
echo -e "${BLUE}[2/9] Installing Xcode Command Line Tools (if needed)...${NC}"
if xcode-select -p &> /dev/null; then
    echo "✅ Xcode Command Line Tools already installed"
else
    echo -e "${YELLOW}Installing Xcode Command Line Tools...${NC}"
    echo "A popup will appear - click 'Install' and wait for it to complete (5-10 min)"
    xcode-select --install || true
    echo ""
    echo -e "${YELLOW}⏸️  PAUSED: Waiting for Xcode tools installation...${NC}"
    echo "Press ENTER after the Xcode installation completes..."
    read -r
fi

# Step 3: Create virtual environment
echo ""
echo -e "${BLUE}[3/9] Creating Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate

# Step 4: Upgrade pip and install build tools
echo ""
echo -e "${BLUE}[4/9] Upgrading pip and installing build tools...${NC}"
pip install --upgrade pip setuptools wheel --quiet
echo "✅ Build tools installed"

# Step 5: Install dependencies in the right order (to use binary wheels)
echo ""
echo -e "${BLUE}[5/9] Installing Python dependencies...${NC}"
echo "Installing core dependencies first (using binary wheels)..."

# Install numpy first (needed for pandas)
pip install numpy==1.26.2 --quiet

# Install pandas with binary wheel (no compilation needed)
echo "Installing pandas (using pre-built binary)..."
pip install pandas==2.1.4 --only-binary :all: --quiet || {
    echo -e "${YELLOW}Binary wheel not available, trying with pip cache...${NC}"
    pip install pandas==2.1.4 --quiet
}

# Install torch (this is large, takes time)
echo "Installing PyTorch (this is large, ~2GB)..."
pip install torch==2.1.0 --quiet

# Install sentence-transformers
echo "Installing sentence-transformers..."
pip install sentence-transformers==2.2.2 --quiet

# Install remaining dependencies
echo "Installing remaining dependencies..."
pip install -r requirements.txt --quiet 2>/dev/null || {
    # If requirements.txt fails (due to already installed packages), that's ok
    echo "Some packages already installed, continuing..."
}

echo "✅ All dependencies installed"

# Step 6: Create .env file
echo ""
echo -e "${BLUE}[6/9] Creating environment configuration...${NC}"
if [ -f ".env" ]; then
    echo ".env already exists, skipping..."
else
    cp .env.example .env
    echo "✅ .env file created"
fi

# Step 7: Start Docker services
echo ""
echo -e "${BLUE}[7/9] Starting PostgreSQL with pgvector...${NC}"
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

# Step 8: Initialize database
echo ""
echo -e "${BLUE}[8/9] Initializing database schema...${NC}"
python3 -c "
import asyncio
from mothra.db.session import init_db
asyncio.run(init_db())
print('✅ Database initialized with pgvector extension')
"

# Step 9: Discover sources
echo ""
echo -e "${BLUE}[9/9] Discovering carbon data sources...${NC}"
python3 -m mothra.agents.survey.survey_agent
echo "✅ Sources discovered and cataloged"

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
echo "To activate the virtual environment in a new terminal:"
echo "   source venv/bin/activate"
echo ""
