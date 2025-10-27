# EC3 OAuth2 "invalid_client" Error - Quick Fix Summary

## Problem
All OAuth2 token requests are failing with `invalid_client` (HTTP 401)

## Root Cause
The OAuth2 client credentials are being rejected by EC3's server. This means:
- The OAuth2 application may be deleted/disabled
- Client credentials are incorrect or revoked
- Password Grant flow may not be enabled

## Immediate Actions

### Option 1: Fix OAuth2 (Recommended if you need full API access)

1. **Log into EC3**: https://buildingtransparency.org/
2. **Check OAuth Apps**: https://buildingtransparency.org/ec3/manage-apps
3. **Verify 'mothratest' app**:
   - Does it exist?
   - Is Password Grant enabled?
   - Are credentials correct?
4. **If missing**: Create new OAuth app with Password Grant
5. **Update .env** with correct credentials
6. **Test**: `python test_ec3_credentials.py`

### Option 2: Use API Key (Simpler alternative)

1. **Get API key**: https://buildingtransparency.org/ec3/manage-apps/keys
2. **Update .env**:
   ```bash
   EC3_API_KEY=<your_api_key>
   
   # Comment out OAuth2
   # EC3_OAUTH_CLIENT_ID=...
   # EC3_OAUTH_CLIENT_SECRET=...
   # EC3_OAUTH_USERNAME=...
   # EC3_OAUTH_PASSWORD=...
   ```
3. **Test**: `python test_ec3_credentials.py`

## Test Scripts Created

1. **test_ec3_credentials.py** - Test current credentials
2. **diagnose_oauth_issue.py** - Detailed OAuth2 diagnostics (already exists)
3. **test_ec3_api_key.py** - Test API key authentication

## Documentation

See **EC3_AUTHENTICATION_GUIDE.md** for complete details.

## Current Status

- ❌ OAuth2: Failing with `invalid_client`
- ❌ API Key: Also failed in test (but may need valid key)
- ✓ Code: Already has fallback logic (OAuth2 → API Key → Public)

## Next Steps

1. Choose Option 1 or Option 2 above
2. Fix credentials
3. Run `python test_ec3_credentials.py`
4. If successful, proceed with EC3 integration

---
**Created**: 2025-10-27
