#!/bin/bash
# Quick runner script for EPD Vector Store Loader
#
# Usage examples:
#   ./scripts/run_epd_loader.sh                    # Load all EPDs
#   ./scripts/run_epd_loader.sh --limit 100        # Load first 100 EPDs (for testing)
#   ./scripts/run_epd_loader.sh --skip-existing    # Skip already loaded EPDs
#   ./scripts/run_epd_loader.sh --help             # Show all options

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo "Checking dependencies..."
pip install -q -e .

# Check environment variables
if [ -z "$EC3_API_KEY" ] && [ -z "$EC3_OAUTH_USERNAME" ]; then
    echo "WARNING: EC3 credentials not found in environment!"
    echo "Please set either:"
    echo "  EC3_API_KEY=your_api_key"
    echo "or:"
    echo "  EC3_OAUTH_USERNAME=username"
    echo "  EC3_OAUTH_PASSWORD=password"
    echo ""
    echo "Get your API key from: https://buildingtransparency.org/api"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -q 2>/dev/null; then
    echo "WARNING: PostgreSQL doesn't appear to be running"
    echo "Make sure your database is accessible"
fi

echo "Starting EPD Vector Store Loader..."
echo "=================================="

# Run the loader with all arguments passed through
python scripts/load_epds_to_vector_store.py "$@"

echo "=================================="
echo "Done!"
