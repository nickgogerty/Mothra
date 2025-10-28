#!/bin/bash
# Fix dependency conflicts and reinstall packages with correct versions
#
# This script resolves the FastAPI/Starlette version conflict by:
# 1. Uninstalling conflicting packages
# 2. Reinstalling with correct version constraints

set -e

echo "=================================================="
echo "MOTHRA Dependency Fix Script"
echo "=================================================="
echo ""

echo "Fixing FastAPI/Starlette version conflict..."
echo ""

# Uninstall potentially conflicting packages
echo "1. Removing potentially conflicting packages..."
pip uninstall -y fastapi starlette uvicorn 2>/dev/null || true
echo "   ✓ Removed existing installations"
echo ""

# Install with correct version constraints
echo "2. Installing FastAPI with compatible Starlette version..."
pip install "fastapi==0.115.6" "starlette>=0.40.0,<0.42.0" "uvicorn[standard]==0.25.0"
echo "   ✓ Installed compatible versions"
echo ""

# Verify installation
echo "3. Verifying installation..."
python -c "import fastapi; import starlette; print(f'FastAPI: {fastapi.__version__}'); print(f'Starlette: {starlette.__version__}')"
echo "   ✓ Verification complete"
echo ""

echo "=================================================="
echo "Dependency fix completed successfully!"
echo "=================================================="
echo ""
echo "You can now install the rest of the requirements:"
echo "  pip install -r requirements.txt"
echo ""
