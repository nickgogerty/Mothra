# EC3 API Diagnostic Instructions

## Current Situation

You have **17,275 entities** in your database, but the EC3 bulk import is returning **0 EPDs** for all categories.

**Good news**: You already have 990 entities from "EC3 Building Transparency", so your API key works! The issue is with how we're querying the API for bulk imports.

---

## Step 1: Pull Latest Code

```bash
cd ~/Mothra  # Or wherever your Mothra folder is

# Pull the latest changes
git pull origin claude/mothra-carbon-database-011CUSGHTrH9htbUpPmK5pdM
```

You should see:
```
Updating 95358af..dbc6ffe
Fast-forward
 scripts/database_summary.py   |   2 +-
 scripts/diagnose_ec3_api.py   | 276 +++++++++++++++
 2 files changed, 277 insertions(+), 1 deletion(-)
```

---

## Step 2: Run Diagnostic Tool

This will show us what the EC3 API actually returns:

```bash
# Activate your venv
source venv/bin/activate

# Run diagnostic
python scripts/diagnose_ec3_api.py
```

---

## What the Diagnostic Will Show

The script tests 6 different approaches:

### Test 1: Basic EPD List
- No filters, just get 5 EPDs
- Shows: Response type (dict vs list), structure, keys

### Test 2: Category Parameter
- Tests `category='Concrete'`
- Shows if this parameter works

### Test 3: Category Case Sensitivity
- Tests: `concrete`, `Concrete`, `CONCRETE`
- Shows which format works

### Test 4: Query Parameter
- Tests `q='Concrete'` instead of `category`
- Alternative search method

### Test 5: Pagination
- Tests `offset` and `limit`
- Shows pagination structure (`next`, `previous`, `count` fields)

### Test 6: Materials Endpoint
- Tests `/api/materials` instead of `/api/epds`
- Alternative endpoint

---

## Expected Diagnostic Output

### Good Response (API Working):
```
📦 TEST 1: List EPDs (no filters, limit=5)
--------------------------------------------------------------------------------
Status: 200
Content-Type: application/json
Response Type: <class 'dict'>
Dict Keys: ['results', 'count', 'next', 'previous']
Results Count: 5
Total Count: 87234

First 500 chars of response:
{
  "count": 87234,
  "next": "https://openepd.buildingtransparency.org/api/epds?limit=5&offset=5",
  "previous": null,
  "results": [
    {
      "id": "abc123",
      "name": "Portland Cement CEM I",
      ...
    }
  ]
}
```

### Bad Response (Wrong Parameters):
```
📦 TEST 2: Search with category='Concrete'
--------------------------------------------------------------------------------
Status: 200
Response Type: <class 'dict'>
Results Count: 0           ← PROBLEM: 0 results
```

---

## Common Scenarios

### Scenario A: API Returns Dict with 'results' Key

```python
{
  "count": 87234,
  "results": [...]
}
```

**Fix**: Our code should work! The issue might be parameter names.

### Scenario B: API Returns List Directly

```python
[
  {"id": "abc", "name": "..."},
  {"id": "def", "name": "..."}
]
```

**Fix**: We already handle this! Check if Test 1 shows data.

### Scenario C: Wrong Parameter Names

```
category='Concrete' → 0 results
q='Concrete' → 5 results
```

**Fix**: Need to use `q` parameter instead of `category`.

### Scenario D: Case Sensitivity Issue

```
category='Concrete' → 0 results
category='concrete' → 5 results
```

**Fix**: Need to lowercase category names.

---

## Step 3: Share Diagnostic Output

After running the diagnostic, **share the output with me**. It will show:

1. What response structure the API uses
2. Which parameters actually work
3. Whether the issue is:
   - Wrong parameter names
   - Case sensitivity
   - Empty results for those categories
   - Permissions issue with API key

---

## Step 4: I'll Fix the Code

Once I see the diagnostic output, I'll:

1. Update `ec3_integration.py` with correct parameters
2. Fix any case sensitivity issues
3. Ensure we're using the right endpoint
4. Test the fix works

---

## Your Current Database Composition

Based on your `database_summary.py` output:

```
Total Entities:        17,275
Verified EPDs:              0
Data Sources:              45

BY SOURCE:
- UK DEFRA Full Conversion Factors 2024      5,082 entities
- UK DEFRA 2024 GHG Conversion Factors        4,069 entities
- EPA GHGRP Full Dataset 2023                 3,285 entities
- EPA GHGRP 2023 Emissions Data               3,006 entities
- EC3 Building Transparency                     990 entities  ← Some EC3 data!
- EIA Energy-Related CO2 Emissions              822 entities

BY TYPE:
- process (75.5%)        13,050 entities
- transport (10.2%)       1,763 entities
- energy (8.5%)           1,469 entities
- material (5.7%)           993 entities

BY CATEGORY:
- uncategorized (75.2%)  12,988 entities
- energy (11.7%)          2,014 entities
- transport (10.3%)       1,782 entities
- road (6.0%)             1,041 entities
- construction (5.7%)       990 entities  ← Your EC3 EPDs

BY GEOGRAPHY:
- Global (97.7%)         16,873 entities
- UK (2.0%)                 342 entities
- EU (0.3%)                  53 entities
```

---

## What This Tells Us

### Good Signs:
✅ You have 990 entities from EC3 already imported
✅ Your API key works
✅ Database is growing (17k entities)
✅ Good data diversity (government + EPD sources)

### The Issue:
❌ Bulk import getting 0 EPDs per category
❌ Parameter names or values might be wrong
❌ Need to understand exact API query format

### Your 990 EC3 Entities:
- Type: `material` (993 materials, ~990 from EC3)
- Category: `construction`
- Geography: Mostly `Global`

These were likely imported with different query parameters than the bulk import is using.

---

## After Diagnostic

Once you share the diagnostic output, I'll:

1. **Identify the issue** - Wrong params? Case sensitivity? Empty results?
2. **Fix the code** - Update ec3_integration.py with correct approach
3. **Test the fix** - Ensure EPDs import successfully
4. **Full import** - Get you to 100k entities

---

## Troubleshooting

### If Diagnostic Fails to Run:

```bash
# Check API key is set
cat .env | grep EC3_API_KEY

# Should show:
# EC3_API_KEY=JAWnY2CsrYkXcX4m7xQGb7zbmMstPx

# If not set:
echo 'EC3_API_KEY=JAWnY2CsrYkXcX4m7xQGb7zbmMstPx' >> .env
```

### If You Get Import Errors:

```bash
# Install dependencies
pip install aiohttp

# Or full requirements
pip install -r requirements.txt
```

### If Database Summary Still Errors:

```bash
# Pull latest fix
git pull origin claude/mothra-carbon-database-011CUSGHTrH9htbUpPmK5pdM

# The embedding field name is now fixed
python scripts/database_summary.py
```

---

## Summary

| Task | Command | Purpose |
|------|---------|---------|
| **Pull code** | `git pull origin claude/mothra-carbon-database-011CUSGHTrH9htbUpPmK5pdM` | Get diagnostic tool |
| **Run diagnostic** | `python scripts/diagnose_ec3_api.py` | See what API returns |
| **Check database** | `python scripts/database_summary.py` | See current composition |
| **Share output** | Copy/paste diagnostic results | So I can fix the code |

---

## What I Need From You

**Run the diagnostic and share the full output.** It will look like:

```
================================================================================
EC3 API DIAGNOSTIC TOOL
================================================================================
API Key: JAWnY2CsrY...Px

📦 TEST 1: List EPDs (no filters, limit=5)
--------------------------------------------------------------------------------
Status: 200
Content-Type: application/json
Response Type: <class 'dict'>
...

📦 TEST 2: Search with category='Concrete'
--------------------------------------------------------------------------------
Status: 200
Response Type: <class 'dict'>
Results Count: 0  ← This is the key info!
...

[etc]
```

This will tell me exactly what's wrong and how to fix it!

---

**Last Updated**: 2025-10-27
**Commit**: `dbc6ffe`
**Branch**: `claude/mothra-carbon-database-011CUSGHTrH9htbUpPmK5pdM`
