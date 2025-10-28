#!/bin/bash
#
# Comprehensive EPD Loader Wrapper Script
# ========================================
# Convenient wrapper for running the comprehensive EPD loader with common options.
#
# Usage:
#   ./scripts/run_comprehensive_epd_loader.sh                    # Load all EPDs
#   ./scripts/run_comprehensive_epd_loader.sh --limit 100       # Test with 100 EPDs
#   ./scripts/run_comprehensive_epd_loader.sh --skip-existing   # Skip already loaded
#   ./scripts/run_comprehensive_epd_loader.sh --help            # Show all options
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Comprehensive EPD Loader${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if .env file exists
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}✗ Error: .env file not found${NC}"
    echo "  Please copy .env.example to .env and configure your credentials"
    echo "  cp .env.example .env"
    exit 1
fi

# Check if Python virtual environment exists
if [ -d "$PROJECT_DIR/venv" ]; then
    echo -e "${GREEN}✓ Activating virtual environment${NC}"
    source "$PROJECT_DIR/venv/bin/activate"
else
    echo -e "${YELLOW}⚠ Warning: Virtual environment not found at $PROJECT_DIR/venv${NC}"
    echo "  Continuing with system Python..."
fi

# Verify system readiness
echo ""
echo -e "${BLUE}Step 1: Verifying system readiness...${NC}"
echo ""

if ! python "$SCRIPT_DIR/verify_system_ready.py"; then
    echo ""
    echo -e "${RED}✗ System verification failed${NC}"
    echo "  Please fix the issues above before loading EPDs"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ System verification passed${NC}"
echo ""

# Confirm with user
if [ "$1" != "--yes" ] && [ "$1" != "-y" ]; then
    echo -e "${YELLOW}This will load EPDs from EC3 API into the database.${NC}"
    echo ""
    echo "Options passed: $@"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Run the loader
echo ""
echo -e "${BLUE}Step 2: Loading EPDs...${NC}"
echo ""

# Remove --yes/-y from args if present
ARGS=()
for arg in "$@"; do
    if [ "$arg" != "--yes" ] && [ "$arg" != "-y" ]; then
        ARGS+=("$arg")
    fi
done

if python "$SCRIPT_DIR/load_epds_comprehensive.py" "${ARGS[@]}"; then
    echo ""
    echo -e "${GREEN}✓ EPD loading completed successfully!${NC}"
    echo ""

    # Offer to generate summary report
    echo -e "${BLUE}Step 3: Generate summary report?${NC}"
    read -p "Generate summary report now? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo ""
        python "$SCRIPT_DIR/epd_summary_report.py"
    fi

    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}All Done!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo "Log files are in: $PROJECT_DIR/logs/"
    echo ""
    echo "Next steps:"
    echo "  - View summary report: python scripts/epd_summary_report.py"
    echo "  - Test semantic search: python scripts/query_epd_vector_store.py \"your query\""
    echo ""

    exit 0
else
    echo ""
    echo -e "${RED}✗ EPD loading failed${NC}"
    echo ""
    echo "Check the log files for details:"
    echo "  $PROJECT_DIR/logs/epd_loading_detailed_*.log"
    echo "  $PROJECT_DIR/logs/epd_loading_summary_*.log"
    echo ""
    exit 1
fi
