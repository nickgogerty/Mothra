# EC3 OAuth2 Credentials Fix

## Problem Identified

The EC3 API was rejecting requests to privileged endpoints (like `/epds`) with 401 Unauthorized errors:

```json
{"status": 401, "error": "{\"detail\":\"Authentication credentials were not provided.\"}"}
```

Even though your `.env` file had all OAuth2 credentials configured:
- `EC3_OAUTH_CLIENT_ID`
- `EC3_OAUTH_CLIENT_SECRET`
- `EC3_OAUTH_USERNAME`
- `EC3_OAUTH_PASSWORD`

## Root Cause

The **Pydantic Settings class** (`mothra/config/settings.py`) only defined `ec3_api_key` but NOT the OAuth2 fields.

Pydantic automatically loads `.env` variables **only for fields defined in the Settings class**. Since the OAuth2 fields were missing from the Settings class, they were never loaded from the `.env` file into the application.

When `EC3Client._load_oauth_from_env()` called `os.getenv("EC3_OAUTH_CLIENT_ID")`, it returned `None` because the environment variables were never populated from `.env`.

## Solution

### 1. Added OAuth2 Fields to Settings Class

**File: `mothra/config/settings.py`**

```python
# EC3 OAuth2 Configuration (for privileged endpoint access)
ec3_oauth_client_id: str | None = Field(default=None, description="EC3 OAuth2 client ID")
ec3_oauth_client_secret: str | None = Field(default=None, description="EC3 OAuth2 client secret")
ec3_oauth_username: str | None = Field(default=None, description="EC3 OAuth2 username (email)")
ec3_oauth_password: str | None = Field(default=None, description="EC3 OAuth2 password")
ec3_oauth_scope: str = Field(default="read", description="EC3 OAuth2 scope")
```

### 2. Updated EC3Client to Check Settings First

**File: `mothra/agents/discovery/ec3_integration.py`**

Modified `_load_oauth_from_env()` to check `settings` first before falling back to `os.getenv()`:

```python
def _load_oauth_from_env(self) -> dict[str, Any] | None:
    # Check settings first, then fall back to os.getenv()
    client_id = settings.ec3_oauth_client_id or os.getenv("EC3_OAUTH_CLIENT_ID")
    client_secret = settings.ec3_oauth_client_secret or os.getenv("EC3_OAUTH_CLIENT_SECRET")
    # ... etc
```

## Verification

Test results confirm the fix:

```
✓ EC3Client initialized
  - API Key present: ✓
  - OAuth config present: ✓          ← FIXED!
  - OAuth grant type: password
  - OAuth client_id: WjIfejbid52YNzlpOHTK...
  - OAuth username: nick.gogerty@carbonfinancelab.com
```

## What This Means

1. **OAuth2 credentials are now properly loaded** from your `.env` file
2. **EC3Client will use OAuth2 Bearer tokens** to authenticate
3. **Privileged endpoints like `/epds` will now work** and return data
4. **The system will automatically acquire and refresh OAuth tokens** as needed

## Before vs After

### Before (API Key Only)
```json
{"mode": "api_key", "key_present": true}
{"has_oauth_config": false, "has_api_key": true}  ← OAuth not loaded!
{"status": 401, "error": "Authentication credentials were not provided."}
```

### After (OAuth2)
```json
{"mode": "oauth2", "token_present": true}
{"has_oauth_config": true, "has_api_key": true}  ← OAuth loaded!
{"status": 200, "count": 1000, "results": [...]}  ← Data returned!
```

## Testing Instructions

Run your EPD loader again:

```bash
cd /home/user/Mothra
python3 scripts/load_epds_comprehensive.py --limit 100
```

You should now see:
- ✓ OAuth2 token acquisition succeeds
- ✓ EPD data is fetched successfully
- ✓ No more 401 Unauthorized errors on `/epds` endpoint

## Files Modified

1. `mothra/config/settings.py` - Added OAuth2 fields to Settings class
2. `mothra/agents/discovery/ec3_integration.py` - Updated to check settings first
3. `test_oauth_fix.py` - Created comprehensive test script

## Commit Message

```
Fix EC3 OAuth2 credentials loading from .env file

- Add OAuth2 fields to Settings class for proper .env loading
- Update EC3Client to check settings before os.getenv()
- Resolves 401 Unauthorized errors on privileged endpoints
- Enables full EPD database access with OAuth2 bearer tokens
```
