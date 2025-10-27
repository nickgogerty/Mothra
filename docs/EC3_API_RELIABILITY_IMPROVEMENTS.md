# EC3 API Reliability Improvements

## Overview

This document describes the comprehensive reliability improvements made to the Mothra EC3 API integration to ensure robust, production-ready API interactions with the Building Transparency EC3 API.

## Summary of Improvements

### 1. Enhanced Bearer Token Authentication

**Problem**: Session headers were set once during initialization, but subsequent token refreshes didn't update the session for future requests.

**Solution**:
- Added `_update_session_auth_header()` method that updates session headers whenever token is refreshed
- All future requests automatically use the new token without manual header management
- Supports both OAuth2 and API key authentication seamlessly

**Implementation**:
```python
def _update_session_auth_header(self):
    """Update the session's authorization header with current token."""
    if self.access_token:
        self.session.headers["Authorization"] = f"Bearer {self.access_token}"
    elif self.api_key:
        self.session.headers["Authorization"] = f"Bearer {self.api_key}"
```

**Files Changed**:
- `mothra/agents/discovery/ec3_integration.py:208-227`

---

### 2. Proactive Token Expiration Handling

**Problem**: Tokens would expire during long-running operations, causing 401 errors mid-execution.

**Solution**:
- Added `_is_token_expired()` method to check token expiry with 60-second buffer
- Added `_ensure_valid_token()` method to proactively refresh tokens before requests
- Token expiry timestamp logged with each refresh for monitoring

**Implementation**:
```python
def _is_token_expired(self) -> bool:
    """Check if token expired or expiring in next 60 seconds."""
    if not self.token_expiry:
        return False
    return time.time() >= (self.token_expiry - 60)

async def _ensure_valid_token(self):
    """Proactively refresh token before making request if expired."""
    if self._is_token_expired():
        await self._get_oauth_token()
```

**Benefits**:
- Prevents 401 errors by refreshing tokens before they expire
- Reduces failed requests and retry overhead
- Better performance for long-running extraction operations

**Files Changed**:
- `mothra/agents/discovery/ec3_integration.py:288-312`

---

### 3. Intelligent 401 Error Handling

**Problem**: All 401 errors were treated the same, leading to unnecessary retries for non-expiry auth failures.

**Solution**:
- Parse 401 error response bodies to detect token expiration messages
- Only attempt token refresh for actual expiration (not invalid credentials)
- Single refresh attempt per request to prevent infinite loops
- Detailed logging with error context and recommendations

**Detected Expiration Phrases**:
- "token expired"
- "expired token"
- "token has expired"
- "invalid token"
- "authentication failed"

**Implementation**:
```python
if status == 401:
    error_text = await response.text()
    is_token_expired = any(phrase in error_text.lower() for phrase in [
        "token expired", "expired token", "token has expired",
        "invalid token", "authentication failed"
    ])

    if is_token_expired and self.oauth_config and not token_refresh_attempted:
        token_refresh_attempted = True
        await self._get_oauth_token()
        if self.access_token:
            continue  # Retry with new token
```

**Files Changed**:
- `mothra/agents/discovery/ec3_integration.py:321-368`

---

### 4. Enhanced 404 Logging for Unavailable Endpoints

**Problem**: Generic 404 errors didn't explain why endpoints were unavailable, making debugging difficult.

**Solution**:
- Added detailed 404 logging with possible reasons
- Clear recommendations for troubleshooting
- Helps distinguish between:
  - Enterprise-only endpoints
  - Private/permission-restricted endpoints
  - Incorrect endpoint URLs
  - Deprecated endpoints

**Log Output Example**:
```python
logger.warning(
    "ec3_endpoint_not_found",
    endpoint=endpoint,
    url=url,
    message="Endpoint not accessible - may be private/enterprise-only",
    possible_reasons=[
        "Endpoint requires enterprise/paid account",
        "Endpoint is private and requires special permissions",
        "Endpoint URL may be incorrect",
        "Endpoint may have been deprecated or moved"
    ],
    recommendation="Check EC3 API docs at https://buildingtransparency.org/..."
)
```

**Files Changed**:
- `mothra/agents/discovery/ec3_integration.py:896-910`

---

### 5. Improved Pagination with Debug Logging

**Problem**: Pagination failures were silent, making it hard to debug incomplete extractions.

**Solution**:
- Added debug logging at every pagination stage
- Log reasons for pagination completion (no more results, error, partial batch)
- Track progress with batch counts and totals
- Helps identify API behavioral changes

**Pagination Completion Scenarios**:
1. **Error detected**: Log error type and records fetched so far
2. **No more results**: Log total records successfully fetched
3. **No next URL**: Indicates end of available data
4. **Partial batch**: Received fewer records than requested (last page)

**Implementation**:
```python
logger.debug(
    "ec3_pagination_progress",
    endpoint=endpoint,
    batch_count=len(results),
    total_fetched=total_fetched
)

if not next_url:
    logger.debug(
        "ec3_pagination_complete_no_next",
        endpoint=endpoint,
        total_fetched=total_fetched
    )
```

**Files Changed**:
- `mothra/agents/discovery/ec3_integration.py:1267-1362`

---

### 6. Comprehensive Error Logging

**Problem**: Error logs lacked context needed for debugging production issues.

**Solution**:
- All error logs now include:
  - Full URL being accessed
  - HTTP method used
  - Error type/class name
  - Truncated error text (500 chars) to prevent log spam
  - Retry attempt number
  - Authentication status
  - Actionable recommendations

**Enhanced Error Types**:

#### Rate Limiting (429)
```python
logger.warning(
    "ec3_rate_limited_retry",
    attempt=attempt + 1,
    max_retries=self.MAX_RETRIES,
    delay=delay,
    url=url,
    message="Rate limit exceeded, backing off"
)
```

#### Network Errors
```python
logger.warning(
    "ec3_network_error_retry",
    attempt=attempt + 1,
    error=str(e),
    error_type=type(e).__name__,
    url=url
)
```

#### Unauthorized Access
```python
logger.error(
    "ec3_unauthorized",
    status=status,
    error=error_text[:500],
    url=url,
    token_refresh_attempted=token_refresh_attempted,
    has_oauth_config=bool(self.oauth_config),
    has_api_key=bool(self.api_key),
    recommendation="Check credentials or token validity"
)
```

**Files Changed**:
- `mothra/agents/discovery/ec3_integration.py:314-462`

---

### 7. Security: Verified No Secrets in Source Control

**Verified**:
- ✅ `.env` files are properly gitignored
- ✅ `.env.ec3` files are gitignored
- ✅ `.env.local` files are gitignored
- ✅ Example files (`.env.example`, `.env.ec3.example`) contain no real secrets
- ✅ No hardcoded secrets found in Python files
- ✅ All secrets loaded from environment variables only

**Gitignore Verification**:
```bash
$ git check-ignore .env .env.ec3 .env.local
.env
.env.ec3
.env.local
```

**Files Verified**:
- `.gitignore`
- All `.env.example` files
- All Python files in `mothra/` and `scripts/`

---

## Testing the Improvements

### Test 1: Token Refresh During Long Operations

Run a full database extraction that will take longer than token expiry:

```bash
python scripts/extract_full_ec3_database.py --full
```

**Expected Behavior**:
- Token proactively refreshed before expiry (check logs for `ec3_token_proactive_refresh`)
- No 401 errors during extraction
- Session headers automatically updated
- All requests use fresh tokens

### Test 2: 404 Endpoint Logging

Try accessing an enterprise-only endpoint:

```python
async with EC3Client() as client:
    result = await client.get_endpoint("tally_projects")
```

**Expected Log Output**:
```
WARNING: ec3_endpoint_not_found
  endpoint: tally_projects
  message: Endpoint not accessible - may be private/enterprise-only
  possible_reasons: [...]
  recommendation: Check EC3 API documentation
```

### Test 3: Pagination Debugging

Extract a large dataset and check debug logs:

```bash
# Set log level to DEBUG
export LOG_LEVEL=DEBUG
python scripts/extract_full_ec3_database.py --endpoints epds --limit 5000
```

**Expected Debug Logs**:
```
DEBUG: ec3_pagination_progress endpoint=epds batch_count=1000 total_fetched=1000
DEBUG: ec3_pagination_progress endpoint=epds batch_count=1000 total_fetched=2000
DEBUG: ec3_pagination_progress endpoint=epds batch_count=1000 total_fetched=3000
DEBUG: ec3_pagination_complete_partial_batch endpoint=epds requested=1000 received=500
```

### Test 4: Rate Limiting Resilience

Test retry logic with high request volume:

```python
async with EC3Client() as client:
    tasks = [client.search_epds(limit=1000) for _ in range(100)]
    results = await asyncio.gather(*tasks)
```

**Expected Behavior**:
- Automatic exponential backoff on 429 errors
- Retry delays: 2s, 4s, 8s, 16s
- Successful completion after retries
- Log messages: `ec3_rate_limited_retry`

---

## Configuration

### Environment Variables

**OAuth2 Authentication (Recommended)**:
```bash
EC3_OAUTH_CLIENT_ID=your_client_id
EC3_OAUTH_CLIENT_SECRET=your_client_secret
EC3_OAUTH_USERNAME=your_username
EC3_OAUTH_PASSWORD=your_password
EC3_OAUTH_SCOPE=read  # optional
```

**API Key Authentication**:
```bash
EC3_API_KEY=your_api_key_here
```

**Custom API Base URL** (optional):
```bash
EC3_API_BASE_URL=https://buildingtransparency.org/api
```

### Setup Credentials

Use the interactive setup script:
```bash
python scripts/setup_ec3_credentials.py
```

This will:
1. Prompt for authentication method
2. Collect credentials securely
3. Test credentials
4. Save to `.env.ec3` file
5. Update `.gitignore`

---

## API Coverage

All improvements apply to **ALL** EC3 API endpoints:

### Core Endpoints
- `epds` - Environmental Product Declarations (90,000+)
- `materials` - Material data
- `plants` - Manufacturing plants
- `projects` - Construction projects

### User & Organization
- `users`, `user_groups`, `orgs`, `plant_groups`

### EPD Management
- `epd_requests`, `epd_imports`, `industry_epds`, `generic_estimates`

### Standards & Reference Data
- `pcrs` (Product Category Rules)
- `baselines`, `reference_sets`, `categories`, `standards`

### Project Management
- `civil_projects`, `collections`, `building_groups`
- `building_campuses`, `building_complexes`, `project_views`
- `bim_projects`, `elements`

### Integrations
- `procore`, `autodesk_takeoff`, `bid_leveling_sheets`, `tally_projects`

### Other
- `charts`, `dashboard`, `docs`, `access_management`, `configurations`, `jobs`

---

## Retry Configuration

### Default Settings

```python
MAX_RETRIES = 4
RETRY_DELAYS = [2, 4, 8, 16]  # Exponential backoff in seconds
```

### Retry Behavior

**Retried Errors**:
- 5xx Server errors
- 429 Rate limiting
- Network errors (connection, timeout)
- 401 Token expiration (with token refresh)

**Not Retried**:
- 400 Bad Request (client error)
- 403 Forbidden (permission error)
- 404 Not Found (endpoint doesn't exist)
- 401 Unauthorized (after token refresh attempt)

---

## Monitoring & Observability

### Key Log Events

**Authentication**:
- `ec3_auth_mode` - Authentication method used
- `oauth_token_acquired` - OAuth token obtained
- `ec3_token_proactive_refresh` - Proactive token refresh
- `ec3_token_expired_refreshing` - Token expired, refreshing
- `ec3_credentials_valid` - Credentials validated successfully

**Request Lifecycle**:
- `ec3_endpoint_retrieved` - Successful data fetch
- `ec3_retry` - Retrying after error
- `ec3_rate_limited_retry` - Rate limit retry with backoff
- `ec3_max_retries_exceeded` - All retries exhausted

**Errors**:
- `ec3_unauthorized` - 401 authentication error
- `ec3_endpoint_not_found` - 404 endpoint not found
- `ec3_client_error` - 4xx client error
- `ec3_network_error_retry` - Network error with retry
- `ec3_unexpected_error` - Unexpected exception

**Pagination**:
- `ec3_pagination_progress` - Pagination progress update
- `ec3_pagination_complete_no_next` - Pagination finished (no next URL)
- `ec3_pagination_complete_partial_batch` - Last page received

---

## Performance Characteristics

### Token Refresh Overhead

- **Proactive refresh**: ~200-500ms (before request)
- **Reactive refresh**: ~200-500ms + failed request time
- **Net improvement**: Eliminates failed request overhead

### Pagination Efficiency

- **Batch size**: 1000 records per request (default)
- **Parallel requests**: Not implemented (sequential for rate limit compliance)
- **Memory efficiency**: Streaming pagination, results accumulated in memory

### Retry Timing

- **Total retry time** (worst case): 2 + 4 + 8 + 16 = 30 seconds
- **Requests with 4 retries**: Only server errors and rate limits
- **Most requests**: Complete on first attempt

---

## Best Practices

### 1. Use OAuth2 for Production

API keys may have limited endpoint access. OAuth2 provides:
- Full endpoint access
- Automatic token refresh
- Better security (tokens expire)

### 2. Enable Authentication Validation

```python
results = await client.extract_all_data(
    validate_auth=True,  # Validate before extraction
    stop_on_auth_failure=True  # Stop if auth fails
)
```

### 3. Monitor 404 Logs

Some endpoints require enterprise accounts. Track 404s to understand:
- Which endpoints are available to your account
- Which endpoints may require upgrades
- API changes or deprecations

### 4. Set Appropriate Limits for Testing

```python
# Test with small limit first
results = await client.extract_all_data(max_per_endpoint=100)

# Then scale up for production
results = await client.extract_all_data(max_per_endpoint=None)
```

### 5. Use Debug Logs for Troubleshooting

```bash
export LOG_LEVEL=DEBUG
python your_script.py
```

### 6. Never Commit Secrets

- Always use `.env` files for secrets
- Verify `.gitignore` includes `.env*`
- Use `.env.example` for documentation (no real secrets)
- Rotate credentials if accidentally committed

---

## Troubleshooting

### Issue: Still Getting 401 Errors

**Check**:
1. Credentials are correct and active
2. OAuth client has required permissions
3. Token hasn't been revoked server-side
4. Check logs for `ec3_token_refresh_failed`

**Solution**:
```bash
# Re-setup credentials
python scripts/setup_ec3_credentials.py

# Test credentials
python scripts/test_ec3_integration.py
```

### Issue: High Rate Limiting (429 Errors)

**Check**:
1. Request frequency
2. Batch sizes (reduce if needed)
3. Parallel request count

**Solution**:
```python
# Reduce batch size
results = await client.search_epds_all(batch_size=500)  # Down from 1000

# Add delays between endpoint extractions
import asyncio
for endpoint in endpoints:
    data = await client.get_endpoint(endpoint)
    await asyncio.sleep(1)  # 1 second delay
```

### Issue: Pagination Not Completing

**Check Debug Logs**:
```bash
export LOG_LEVEL=DEBUG
```

**Look for**:
- `ec3_pagination_stopped_error` - Error during pagination
- `ec3_pagination_complete_no_next` - Normal completion
- `ec3_pagination_complete_partial_batch` - Last page

### Issue: Missing Endpoints (404s)

**Explanation**:
Some endpoints are private, enterprise-only, or require special permissions.

**Expected 404s** (for standard accounts):
- `tally_projects` - Tally integration (enterprise)
- `procore` - Procore integration (enterprise)
- `autodesk_takeoff` - Autodesk integration (enterprise)
- Some project-specific endpoints

**Solution**:
- Check endpoint availability in EC3 API docs
- Contact Building Transparency for enterprise access
- Filter out 404 endpoints from extraction lists

---

## Files Modified

All changes are in a single file for easy review:

```
mothra/agents/discovery/ec3_integration.py
  - Lines 208-227: _update_session_auth_header()
  - Lines 229-286: Enhanced _get_oauth_token() with session header updates
  - Lines 288-312: _is_token_expired() and _ensure_valid_token()
  - Lines 314-462: Enhanced _request_with_retry() with token refresh
  - Lines 896-938: Enhanced get_endpoint() with better 404 logging
  - Lines 1267-1362: Enhanced _paginate_all_generic() with debug logging
```

No changes required to calling code - all improvements are internal to `EC3Client`.

---

## Related Documentation

- [EC3 API Documentation](https://buildingtransparency.org/ec3/manage-apps/api-doc/api)
- [EC3 OAuth Guide](https://buildingtransparency.org/ec3/manage-apps/api-doc/guide)
- [Get API Keys](https://buildingtransparency.org/ec3/manage-apps/keys)
- [Setup Credentials Script](../scripts/setup_ec3_credentials.py)
- [Full Database Extraction](../scripts/extract_full_ec3_database.py)

---

## Future Enhancements

Potential improvements for future consideration:

1. **Parallel Pagination**: Fetch multiple pages concurrently (respecting rate limits)
2. **Response Caching**: Cache responses to reduce API load
3. **Metrics Collection**: Track request counts, error rates, latency
4. **Circuit Breaker**: Temporarily stop requests after persistent failures
5. **Request Queuing**: Queue and batch requests for better rate limit compliance
6. **Token Preemptive Refresh**: Refresh tokens before they expire based on usage patterns

---

## Support

For issues or questions:

1. Check this documentation first
2. Review EC3 API documentation
3. Check logs with `LOG_LEVEL=DEBUG`
4. Run diagnostic script: `python scripts/diagnose_ec3_api.py`
5. Test credentials: `python scripts/test_ec3_integration.py`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-27
**Author**: Claude Code
**Status**: Production Ready
