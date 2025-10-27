# .env File Format Fix

## Problem

When running `./scripts/run_epd_loader.sh`, the script failed with:
```bash
Loading environment variables from .env file...
.env: line 50: 2: command not found
```

## Root Cause

The `.env` file contained values with spaces and special characters that were not quoted:

```bash
DAILY_UPDATE_CRON=0 2 * * *
WEEKLY_REFRESH_CRON=0 2 * * SUN
EC3_OAUTH_PASSWORD=!uCt@Z4u%9
```

When using `source .env` in bash, unquoted values with spaces are interpreted as separate commands. The line:
```bash
DAILY_UPDATE_CRON=0 2 * * *
```

Was interpreted as:
1. Set `DAILY_UPDATE_CRON=0`
2. Execute command `2` with arguments `* * *`

This caused the error: `.env: line 50: 2: command not found`

## Solution

Added quotes around values containing spaces or special characters:

```bash
DAILY_UPDATE_CRON="0 2 * * *"
WEEKLY_REFRESH_CRON="0 2 * * SUN"
EC3_OAUTH_PASSWORD="!uCt@Z4u%9"
```

## General Rule

When creating `.env` files that will be sourced by bash scripts:

1. **Always quote values with spaces**:
   ```bash
   CRON_SCHEDULE="0 2 * * *"  # ✓ Correct
   CRON_SCHEDULE=0 2 * * *    # ✗ Wrong - will fail
   ```

2. **Quote values with special shell characters** (`!`, `$`, `*`, `?`, `&`, `|`, `;`, `(`, `)`, etc.):
   ```bash
   PASSWORD="p@ss!w0rd"       # ✓ Correct
   PASSWORD=p@ss!w0rd         # ✗ Wrong - special chars will be interpreted
   ```

3. **Simple alphanumeric values don't need quotes**:
   ```bash
   PORT=5432                  # ✓ OK without quotes
   PORT="5432"                # ✓ Also OK with quotes
   ```

4. **Comments must start with `#`**:
   ```bash
   # This is a comment        # ✓ Correct
   PORT=5432 # inline comment # ✗ Wrong - inline comments may cause issues
   ```

## Files Fixed

1. `.env` - User's local environment file (not in git)
2. `.env.example` - Template file committed to git

## Testing

After the fix, the script should load successfully:

```bash
./scripts/run_epd_loader.sh --limit 10
```

Expected output:
```
Loading environment variables from .env file...
Using OAuth2 authentication with client ID: WjIfejbid52YNzlp...
[Script continues normally]
```

## Alternative Loading Methods

If you prefer not to quote values in `.env`, you can use alternative loading methods:

### Python with python-dotenv
```python
from dotenv import load_dotenv
load_dotenv('.env')  # Handles unquoted values correctly
```

### Shell with grep/awk
```bash
while IFS='=' read -r key value; do
    [[ $key =~ ^#.*$ ]] && continue  # Skip comments
    [[ -z $key ]] && continue         # Skip empty lines
    export "$key"="$value"
done < .env
```

Our shell script uses `source .env` for simplicity, which requires proper quoting.
