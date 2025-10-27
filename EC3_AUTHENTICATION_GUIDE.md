# EC3 API Authentication Guide

## Overview

The EC3 API **requires authentication** for most endpoints. Without proper credentials, you'll encounter **401 Unauthorized** errors and won't be able to extract data.

This guide explains how to set up authentication for the Mothra EC3 integration.

---

## Quick Start

### Option 1: Automated Setup (Recommended)

Run the interactive setup wizard:

```bash
python scripts/setup_ec3_credentials.py
```

This wizard will guide you through:
1. Choosing an authentication method
2. Entering your credentials
3. Saving configuration securely
4. Testing your credentials

### Option 2: Manual Setup

1. Copy the example environment file:
```bash
cp .env.ec3.example .env.ec3
```

2. Edit `.env.ec3` with your credentials (see below for details)

3. Load the environment variables:
```bash
export $(cat .env.ec3 | grep -v '^#' | xargs)
```

4. Test your credentials:
```bash
python scripts/test_ec3_api_key.py
```

---

## Authentication Methods

### Method 1: OAuth2 Password Grant (Recommended)

**✅ Advantages:**
- Full access to all EC3 API endpoints
- Best for automated data extraction
- More secure than API keys

**📋 Requirements:**
- EC3 account: https://buildingtransparency.org
- OAuth2 application setup

**Setup Steps:**

1. **Create OAuth2 Application:**
   - Go to: https://buildingtransparency.org/ec3/manage-apps/
   - Click "Create New Application"
   - Fill in:
     - **Name:** "Mothra Data Extraction" (or any name)
     - **Authorization grant type:** "Resource owner password-based"
     - **Client type:** "Confidential"
   - Save and note your **Client ID** and **Client Secret**

2. **Configure Environment Variables:**

Edit `.env.ec3`:
```bash
EC3_OAUTH_CLIENT_ID=your_client_id_here
EC3_OAUTH_CLIENT_SECRET=your_client_secret_here
EC3_OAUTH_USERNAME=your_ec3_username
EC3_OAUTH_PASSWORD=your_ec3_password
EC3_OAUTH_SCOPE=read
```

3. **Load and Test:**
```bash
export $(cat .env.ec3 | grep -v '^#' | xargs)
python scripts/extract_full_ec3_database.py --test
```

---

### Method 2: API Key

**✅ Advantages:**
- Simple setup
- No OAuth app required

**⚠️ Limitations:**
- May have limited endpoint access
- Some endpoints may still return 401/404

**Setup Steps:**

1. **Get API Key:**
   - Go to: https://buildingtransparency.org/ec3/manage-apps/keys
   - Click "Generate New API Key"
   - **Copy the key immediately** (you can't see it again!)

2. **Configure Environment Variable:**

Edit `.env.ec3`:
```bash
EC3_API_KEY=your_api_key_here
```

3. **Load and Test:**
```bash
export $(cat .env.ec3 | grep -v '^#' | xargs)
python scripts/extract_full_ec3_database.py --test
```

---

### Method 3: No Authentication (Public Access)

**⚠️ Not Recommended:**
- Very limited data access
- Most endpoints return 401 Unauthorized
- Only for testing/debugging

No setup required, but expect failures.

---

## Verification

### Check if Credentials are Loaded

```bash
# Check OAuth2
echo $EC3_OAUTH_CLIENT_ID
echo $EC3_OAUTH_USERNAME

# Check API Key
echo $EC3_API_KEY
```

### Test Credentials

```bash
python scripts/test_ec3_api_key.py
```

Expected output with valid credentials:
```
✅ SUCCESS!
   Authentication Method: oauth2
   Message: Authentication valid (oauth2)
   Test Endpoint: orgs
   Records Accessible: 150
```

Expected output with invalid credentials:
```
❌ FAILED!
   Authentication Method: oauth2
   Message: Authentication failed - credentials invalid or expired
```

---

## Troubleshooting

### Problem: 401 Unauthorized Errors

**Symptoms:**
```
❌ materials:
   Status: FAILED
   Error: unauthorized
   Note: Authentication required - set EC3_API_KEY
```

**Solutions:**

1. **Check if credentials are loaded:**
```bash
echo $EC3_OAUTH_CLIENT_ID
echo $EC3_API_KEY
```

2. **Verify credentials are correct:**
   - OAuth2: Check client ID, client secret, username, password
   - API Key: Regenerate if needed

3. **Run setup wizard:**
```bash
python scripts/setup_ec3_credentials.py
```

4. **Test credentials:**
```bash
python scripts/test_ec3_api_key.py
```

---

### Problem: Token Expired

**Symptoms:**
```
Token expired, refreshing...
Authentication required or token expired.
```

**Solution:**
OAuth2 tokens are automatically refreshed by the EC3Client. If this fails:

1. Verify your OAuth2 credentials are still valid
2. Check if your EC3 account is active
3. Re-run the setup wizard

---

### Problem: 404 Not Found on Some Endpoints

**Symptoms:**
```
❌ users:
   Status: FAILED
   Error: not_found
   Note: Endpoint may not exist or requires authentication
```

**Explanation:**
Some endpoints may:
- Not be implemented yet in the EC3 API
- Require special permissions/account tier
- Be organization-specific

**Solution:**
This is normal. Focus on core endpoints that work:
- `epds` - Environmental Product Declarations
- `materials` - Material data
- `plants` - Manufacturing plants
- `orgs` - Organizations (usually accessible)

---

### Problem: OAuth2 App Creation Issues

**Common Issues:**

1. **"Resource owner password-based" not available**
   - You may need to request this feature from Building Transparency
   - Alternative: Use API key method

2. **Can't find OAuth apps page**
   - Direct link: https://buildingtransparency.org/ec3/manage-apps/
   - Make sure you're logged in

3. **Client secret not visible**
   - Copy it immediately when shown
   - If lost, delete the app and create a new one

---

## Security Best Practices

### ✅ DO:
- Store credentials in `.env.ec3` file
- Add `.env.ec3` to `.gitignore`
- Use environment variables
- Use OAuth2 for production systems
- Rotate credentials periodically

### ❌ DON'T:
- Commit credentials to git
- Share credentials publicly
- Hardcode credentials in scripts
- Use public access for production
- Reuse credentials across projects

---

## Loading Credentials in Code

### Automatic Loading (Default)

The `EC3Client` automatically loads credentials from environment variables:

```python
from mothra.agents.discovery.ec3_integration import EC3Client

async with EC3Client() as client:
    # Credentials automatically loaded from environment
    results = await client.extract_all_data()
```

### Manual Configuration

```python
# OAuth2
oauth_config = {
    "grant_type": "password",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "username": "your_username",
    "password": "your_password",
    "scope": "read",
}

async with EC3Client(oauth_config=oauth_config) as client:
    results = await client.extract_all_data()
```

```python
# API Key
async with EC3Client(api_key="your_api_key") as client:
    results = await client.extract_all_data()
```

### Using python-dotenv

```python
from dotenv import load_dotenv
from mothra.agents.discovery.ec3_integration import EC3Client

# Load from .env.ec3
load_dotenv('.env.ec3')

async with EC3Client() as client:
    # Credentials loaded from .env.ec3
    results = await client.extract_all_data()
```

---

## Advanced: Authorization Code Grant

For web applications with OAuth redirect flow:

1. **Create OAuth2 App:**
   - Go to: https://buildingtransparency.org/ec3/manage-apps/
   - Choose "Authorization code" grant type
   - Set redirect URI (e.g., `http://localhost:8080/callback`)

2. **Get Authorization Code:**
   - Redirect user to authorization URL
   - User approves access
   - Get authorization code from redirect

3. **Configure:**
```bash
EC3_OAUTH_CLIENT_ID=your_client_id
EC3_OAUTH_CLIENT_SECRET=your_client_secret
EC3_OAUTH_AUTHORIZATION_CODE=code_from_redirect
```

4. **Use in Code:**
```python
oauth_config = {
    "grant_type": "authorization_code",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "code": "authorization_code",
}

async with EC3Client(oauth_config=oauth_config) as client:
    results = await client.extract_all_data()
```

---

## Summary

| Method | Setup Complexity | Access Level | Recommended For |
|--------|-----------------|--------------|-----------------|
| **OAuth2 Password Grant** | Medium | Full | Production, automation |
| **API Key** | Simple | Limited | Testing, basic usage |
| **Authorization Code** | Complex | Full | Web applications |
| **Public Access** | None | Very Limited | None (not recommended) |

**Recommendation:** Use OAuth2 Password Grant for full EC3 API access.

---

## Getting Help

### Documentation
- EC3 API Docs: https://buildingtransparency.org/ec3/manage-apps/api-doc/api
- OAuth Guide: https://buildingtransparency.org/ec3/manage-apps/api-doc/guide

### Support
- Building Transparency Support: https://buildingtransparency.org/support
- Mothra Issues: https://github.com/nickgogerty/Mothra/issues

### Quick Commands

```bash
# Setup wizard
python scripts/setup_ec3_credentials.py

# Test credentials
python scripts/test_ec3_api_key.py

# Test extraction
python scripts/extract_full_ec3_database.py --test

# Full extraction
python scripts/extract_full_ec3_database.py --full
```

---

**With proper authentication configured, you'll have full access to the EC3 database!** 🎉
