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

# Load .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
else
    echo "WARNING: .env file not found!"
    echo "Please create a .env file with your EC3 credentials"
    echo "See .env.example or .env.ec3.example for reference"
    exit 1
fi

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

# Check environment variables (OAuth2 or API key)
if [ -z "$EC3_API_KEY" ] && [ -z "$EC3_OAUTH_CLIENT_ID" ]; then
    echo "WARNING: EC3 credentials not found in environment!"
    echo "Please configure .env file with either:"
    echo ""
    echo "Option 1 - OAuth2 (Recommended):"
    echo "  EC3_OAUTH_CLIENT_ID=your_client_id"
    echo "  EC3_OAUTH_CLIENT_SECRET=your_client_secret"
    echo "  EC3_OAUTH_USERNAME=your_username"
    echo "  EC3_OAUTH_PASSWORD=your_password"
    echo ""
    echo "Option 2 - API Key:"
    echo "  EC3_API_KEY=your_api_key"
    echo ""
    echo "Run: python scripts/setup_ec3_credentials.py"
    exit 1
fi

# Show which auth method will be used
if [ -n "$EC3_OAUTH_CLIENT_ID" ]; then
    echo "Using OAuth2 authentication with client ID: ${EC3_OAUTH_CLIENT_ID:0:20}..."
elif [ -n "$EC3_API_KEY" ]; then
    echo "Using API key authentication"
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
