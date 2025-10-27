# OAuth2 Credentials Loading Fix

## Problem

The EPD loader and other EC3 scripts were not properly loading OAuth2 credentials from the `.env` file, resulting in:
- Scripts falling back to API key authentication
- 401 "Authentication credentials were not provided" errors when accessing EPDs
- OAuth2 configuration being ignored

## Root Cause

1. The shell script `run_epd_loader.sh` did not load the `.env` file before running
2. Python scripts did not use `python-dotenv` to load environment variables
3. Environment variables were only in the `.env` file, not exported to the shell

## Solution

### 1. Shell Script Fix (`scripts/run_epd_loader.sh`)

Added automatic `.env` file loading at startup:

```bash
# Load .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
else
    echo "WARNING: .env file not found!"
    exit 1
fi
```

Added OAuth2 credential detection:

```bash
# Check for OAuth2 or API key
if [ -n "$EC3_OAUTH_CLIENT_ID" ]; then
    echo "Using OAuth2 authentication with client ID: ${EC3_OAUTH_CLIENT_ID:0:20}..."
elif [ -n "$EC3_API_KEY" ]; then
    echo "Using API key authentication"
fi
```

### 2. Python Script Fixes

Added explicit `.env` loading to:
- `scripts/load_epds_to_vector_store.py`
- `scripts/extract_full_ec3_database.py`
- `scripts/verify_epd_setup.py`

```python
# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # dotenv not available, assume env vars are already set
    pass
```

## Testing

After applying these fixes, the scripts should:

1. Automatically load OAuth2 credentials from `.env`
2. Display: "Using OAuth2 authentication with client ID: WjIfejbid52YNzlp..."
3. Successfully authenticate with EC3 API
4. Access EPD endpoints without 401 errors

## Verification

Run the EPD loader with the fixed scripts:

```bash
./scripts/run_epd_loader.sh --limit 10
```

Expected output:
```
Loading environment variables from .env file...
Using OAuth2 authentication with client ID: WjIfejbid52YNzlp...
Starting EPD Vector Store Loader...
{"mode": "oauth2", "token_present": true, "event": "ec3_auth_mode"...}
EC3 credentials validated successfully (oauth2)
Fetching EPDs at offset 0...
[Success - EPDs fetched]
```

## Files Modified

1. `scripts/run_epd_loader.sh` - Added .env loading and OAuth2 detection
2. `scripts/load_epds_to_vector_store.py` - Added python-dotenv loading
3. `scripts/extract_full_ec3_database.py` - Added python-dotenv loading
4. `scripts/verify_epd_setup.py` - Added python-dotenv loading

## OAuth2 Configuration

The `.env` file should contain:

```bash
# OAuth2 Password Grant Configuration for mothratest app
EC3_OAUTH_CLIENT_ID=WjIfejbid52YNzlpOHTKej9DA8picZt2K4I53Z3W
EC3_OAUTH_CLIENT_SECRET=<your_client_secret>
EC3_OAUTH_USERNAME=nick.gogerty@carbonfinancelab.com
EC3_OAUTH_PASSWORD=<your_password>
EC3_OAUTH_SCOPE=read

# API Key (fallback if OAuth fails)
EC3_API_KEY=<your_api_key>
```

## Notes

- The API key is kept as a fallback in case OAuth2 fails
- The EC3Client automatically detects and uses OAuth2 credentials when available
- OAuth2 provides full access to all EC3 endpoints including EPDs
- The mothratest OAuth application uses "Resource owner password-based" grant type
