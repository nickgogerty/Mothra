#!/bin/bash
# Verification script for SQLAlchemy metadata fix

echo "=========================================="
echo "MOTHRA - Verification Script"
echo "=========================================="
echo ""

# Check if in venv
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment active: $VIRTUAL_ENV"
else
    echo "⚠️  Virtual environment not active"
    echo "   Run: source venv/bin/activate"
    echo ""
    exit 1
fi

echo ""
echo "Testing imports..."
echo ""

# Test 1: Import verification models
echo "1. Testing verification models..."
python -c "from mothra.db.models_verification import CarbonEntityVerification, Scope3Category; print('   ✅ Verification models imported successfully')" 2>&1

if [ $? -ne 0 ]; then
    echo "   ❌ Failed to import verification models"
    exit 1
fi

# Test 2: Import EC3 integration
echo "2. Testing EC3 integration..."
python -c "from mothra.agents.discovery.ec3_integration import EC3Client; print('   ✅ EC3 integration imported successfully')" 2>&1

if [ $? -ne 0 ]; then
    echo "   ❌ Failed to import EC3 integration"
    exit 1
fi

# Test 3: Import dataset discovery
echo "3. Testing dataset discovery..."
python -c "from mothra.agents.discovery.dataset_discovery import DatasetDiscovery; print('   ✅ Dataset discovery imported successfully')" 2>&1

if [ $? -ne 0 ]; then
    echo "   ❌ Failed to import dataset discovery"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ All imports successful!"
echo "=========================================="
echo ""
echo "The SQLAlchemy 'metadata' issue is fixed."
echo ""
echo "You can now run:"
echo "  python scripts/test_ec3_integration.py"
echo "  python scripts/import_ec3_epds.py"
echo "  python scripts/deep_crawl_real_datasets.py"
echo ""
