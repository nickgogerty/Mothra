# Dependency Conflict Resolution

## Issue

When installing MOTHRA dependencies, you may encounter this error:

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
This behaviour is the source of the following dependency conflicts.
fastapi 0.115.6 requires starlette<0.42.0,>=0.40.0, but you have starlette 0.48.0 which is incompatible.
```

## Root Cause

FastAPI version 0.115.x requires Starlette version `>=0.40.0,<0.42.0`, but a newer incompatible version of Starlette (0.48.0) was installed.

## Solution

### Quick Fix

Run the automated fix script:

```bash
bash scripts/fix_dependencies.sh
```

This will:
1. Remove conflicting packages (fastapi, starlette, uvicorn)
2. Reinstall with compatible versions
3. Verify the installation

### Manual Fix

If you prefer to fix manually:

```bash
# Uninstall conflicting packages
pip uninstall -y fastapi starlette uvicorn

# Install with correct versions
pip install "fastapi==0.115.6" "starlette>=0.40.0,<0.42.0" "uvicorn[standard]==0.25.0"

# Verify installation
python -c "import fastapi; import starlette; print(f'FastAPI: {fastapi.__version__}'); print(f'Starlette: {starlette.__version__}')"
```

### Full Installation

After fixing the core dependencies, install all requirements:

```bash
pip install -r requirements.txt
```

## Compatible Versions

The following versions are confirmed to work together:

- **FastAPI**: 0.115.6
- **Starlette**: 0.41.3 (or any version >=0.40.0, <0.42.0)
- **Uvicorn**: 0.25.0

## Updated Requirements

Both `requirements.txt` and `pyproject.toml` have been updated to explicitly specify compatible versions:

### requirements.txt
```txt
# API framework
fastapi==0.115.6
starlette>=0.40.0,<0.42.0  # Required by fastapi 0.115.x
uvicorn[standard]==0.25.0
```

### pyproject.toml
```toml
dependencies = [
    # ...
    "fastapi>=0.115.0",
    "starlette>=0.40.0,<0.42.0",
    "uvicorn[standard]>=0.25.0",
]
```

## Prevention

To prevent this issue in the future:

1. **Use a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Pin dependencies**: The updated requirements files now explicitly pin compatible versions

3. **Use pip-tools** (optional):
   ```bash
   pip install pip-tools
   pip-compile requirements.in -o requirements.txt
   ```

## Verification

After installation, verify everything works:

```bash
# Check versions
python -c "import fastapi; import starlette; print(f'FastAPI: {fastapi.__version__}'); print(f'Starlette: {starlette.__version__}')"

# Expected output:
# FastAPI: 0.115.6
# Starlette: 0.41.3 (or similar, but < 0.42.0)

# Test imports
python -c "from mothra.config import settings; print('✓ Config loaded successfully')"
```

## Related Issues

- FastAPI GitHub: [Starlette version compatibility](https://github.com/tiangolo/fastapi/issues)
- Starlette releases: https://github.com/encode/starlette/releases

## Troubleshooting

### Issue: Still getting conflicts after running fix script

**Solution**: Clear pip cache and try again
```bash
pip cache purge
bash scripts/fix_dependencies.sh
```

### Issue: Permission errors during installation

**Solution**: Use a virtual environment instead of root
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Different Python version

**Solution**: Ensure you're using Python 3.11+
```bash
python --version  # Should be 3.11 or higher
```

## Additional Notes

- This fix was implemented on 2025-10-28
- The issue affects installations that upgraded packages separately
- Fresh installations with the updated requirements.txt should work without issues
- If you encounter other dependency conflicts, please report them as GitHub issues

---

**Status**: ✅ Fixed and tested
**Last Updated**: 2025-10-28
**Tested With**: Python 3.11, FastAPI 0.115.6, Starlette 0.41.3
