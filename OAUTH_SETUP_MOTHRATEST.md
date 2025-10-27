# OAuth2 Configuration - mothratest Application

## Overview

This document records the OAuth2 configuration applied to the Mothra application using the "mothratest" OAuth application registered with Building Transparency.

## Configuration Date

- **Date**: 2025-10-27
- **Application Name**: mothratest
- **Authorization Grant Type**: Resource owner password-based
- **Client Type**: Confidential

## OAuth2 Credentials Configured

The following OAuth2 credentials have been configured in the `.env` file:

```bash
# OAuth2 Password Grant Configuration for mothratest app
EC3_OAUTH_CLIENT_ID=WjIfejbid52YNzlpOHTKej9DA8picZt2K4I53Z3W
EC3_OAUTH_CLIENT_SECRET=<configured>
EC3_OAUTH_USERNAME=nick.gogerty@carbonfinancelab.com
EC3_OAUTH_PASSWORD=<configured>
EC3_OAUTH_SCOPE=read
```

## How It Works

The EC3Client in `mothra/agents/discovery/ec3_integration.py` automatically loads these credentials from environment variables and uses OAuth2 Password Grant flow to:

1. Exchange username/password + client credentials for an access token
2. Use the access token to authenticate API requests to Building Transparency's EC3 API
3. Automatically refresh tokens when they expire
4. Fall back to the API key if OAuth fails

## Authentication Priority

The application uses the following authentication priority:

1. **OAuth2 Password Grant** (preferred) - Full access to all EC3 endpoints
2. **API Key** (fallback) - Limited access if OAuth fails
3. **Public Access** (no auth) - Very restricted access

## Testing the Configuration

To test if the OAuth2 credentials are working:

```bash
python scripts/setup_ec3_credentials.py
# Follow the prompts to test the credentials
```

Or use the EC3Client directly:

```python
from mothra.agents.discovery.ec3_integration import EC3Client

async with EC3Client() as client:
    result = await client.validate_credentials()
    print(f"Valid: {result['valid']}")
    print(f"Auth Method: {result['auth_method']}")
```

## Security Notes

- The `.env` file containing actual credentials is in `.gitignore` and should NEVER be committed to git
- Client secret and password are sensitive - keep them secure
- OAuth tokens automatically expire and are refreshed as needed
- The mothratest application uses "Confidential" client type for enhanced security

## Related Documentation

- EC3_AUTHENTICATION_GUIDE.md - General EC3 authentication guide
- EC3_INTEGRATION_GUIDE.md - EC3 API integration guide
- .env.ec3.example - Example OAuth2 configuration template

## OAuth Application Settings

The "mothratest" OAuth application is configured with:

- **Authorization Grant Type**: Resource owner password-based
- **Client Type**: Confidential
- **Redirect URIs**: (Not required for password grant flow)

This grant type is ideal for server-side applications where you control both the client and resource owner credentials.
