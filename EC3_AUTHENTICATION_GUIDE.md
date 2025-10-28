# EC3 API Authentication Troubleshooting Guide

## Problem Summary

Your OAuth2 authentication to the EC3 (Building Transparency) API is failing with `invalid_client` errors. This is a **server-side rejection** of your OAuth2 client credentials.

## Diagnostic Results

### OAuth2 Status: ❌ FAILED
- **Error**: `invalid_client` (HTTP 401)
- **Attempted Methods**:
  - ✗ Standard OAuth2 Password Grant (form-encoded)
  - ✗ Without explicit scope
  - ✗ Client credentials in Basic Auth header
  - ✗ JSON body (returned `unsupported_grant_type`)

### API Key Status: ❌ FAILED  
- **Error**: `Authentication credentials were not provided` (HTTP 401)
- **Endpoint Tested**: `/api/epds`

## Root Cause Analysis

The `invalid_client` error is **very specific** and indicates ONE of these issues:

1. **OAuth2 Application Deleted/Disabled**
   - The 'mothratest' OAuth2 application may have been deleted or disabled in your EC3 account

2. **Incorrect Credentials**
   - The Client ID or Client Secret in your `.env` file doesn't match what's registered in EC3
   - Credentials may have been regenerated and the old ones revoked

3. **Password Grant Not Enabled**
   - The OAuth2 application may not have the "Password Grant" flow enabled

4. **API Configuration Changed**
   - EC3 may have changed their OAuth2 requirements

## Immediate Action Required

### Step 1: Verify OAuth2 Application

1. Log into EC3: https://buildingtransparency.org/
2. Go to: https://buildingtransparency.org/ec3/manage-apps  
3. Check if 'mothratest' application exists
4. Verify flows enabled include "Password Grant"

### Step 2: Get or Create Valid Credentials

#### If Application Exists:
- Verify Client ID matches your .env
- Regenerate Client Secret if needed
- Ensure Password Grant is enabled

#### If Application Missing - Create New:
1. Create new OAuth Application
2. Name: `mothra-carbon-database`
3. Enable: Resource Owner Password Credentials
4. Copy Client ID and Secret

### Step 3: Alternative - Use API Key

API key authentication is simpler and may be sufficient:

1. Go to: https://buildingtransparency.org/ec3/manage-apps/keys
2. Create or verify API key
3. Update .env:

```bash
# Use API key instead of OAuth2
EC3_API_KEY=<your_api_key>

# Comment out OAuth2 (not working)
# EC3_OAUTH_CLIENT_ID=...
# EC3_OAUTH_CLIENT_SECRET=...
```

## Code Behavior

The EC3Client has automatic fallback:
1. Tries OAuth2 if configured
2. Falls back to API key if OAuth2 fails  
3. Uses public access as last resort

## Testing

```bash
# Test OAuth2
python diagnose_oauth_issue.py

# Test with MOTHRA
python -c "
from mothra.agents.discovery.ec3_integration import EC3Client
import asyncio

async def test():
    async with EC3Client() as client:
        result = await client.validate_credentials()
        print(f'Valid: {result[\"valid\"]}')
        print(f'Method: {result[\"auth_method\"]}')

asyncio.run(test())
"
```

## Support

- EC3 API Docs: https://buildingtransparency.org/ec3/manage-apps/api-doc/api
- Manage Apps: https://buildingtransparency.org/ec3/manage-apps
- API Keys: https://buildingtransparency.org/ec3/manage-apps/keys
