# Mac Installation Fix

If you're getting compilation errors on Mac (especially with pandas), follow these steps:

## Quick Fix

**Run this instead of the regular setup.sh:**

```bash
bash setup_mac_fixed.sh
```

This script:
1. Installs Xcode Command Line Tools (needed for compilation)
2. Uses pre-built binary wheels instead of compiling from source
3. Installs dependencies in the correct order

## Manual Fix (If Script Doesn't Work)

### Step 1: Install Xcode Command Line Tools

```bash
xcode-select --install
```

A popup will appear. Click "Install" and wait 5-10 minutes.

### Step 2: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### Step 4: Install Dependencies in Order

```bash
# Install numpy first
pip install numpy==1.26.2

# Install pandas using binary wheel (no compilation)
pip install pandas==2.1.4 --only-binary :all:

# Install torch
pip install torch==2.1.0

# Install sentence-transformers
pip install sentence-transformers==2.2.2

# Install remaining dependencies
pip install -r requirements.txt
```

### Step 5: Continue with Normal Setup

```bash
# Create .env
cp .env.example .env

# Start PostgreSQL
docker compose up -d postgres
sleep 10

# Initialize database
python -c "import asyncio; from mothra.db.session import init_db; asyncio.run(init_db())"

# Discover sources
python -m mothra.agents.survey.survey_agent
```

## Why This Happens

The error occurs because:
1. **Missing build tools**: Mac doesn't have C compilers by default
2. **pandas needs compilation**: When installing from source, pandas needs to compile Cython extensions
3. **Xcode tools required**: Apple's Xcode Command Line Tools provide the necessary compilers

## Alternative: Use Anaconda (Easier for Mac)

If you keep having issues, use Anaconda instead:

```bash
# Install Anaconda from https://www.anaconda.com/download

# Create environment
conda create -n mothra python=3.11 -y
conda activate mothra

# Install with conda (has pre-built binaries)
conda install pandas numpy -y
pip install -r requirements.txt
```

## Verify It Worked

```bash
python -c "import pandas; print(f'✅ Pandas {pandas.__version__} installed successfully')"
python -c "import sentence_transformers; print('✅ Sentence-transformers working')"
```

You should see:
```
✅ Pandas 2.1.4 installed successfully
✅ Sentence-transformers working
```

## Still Having Issues?

Try the **absolute minimal install**:

```bash
# Use older, more compatible versions
pip install pandas==2.0.0
pip install numpy==1.24.0
```

Or **skip pandas** temporarily (MOTHRA can work without it for CSV parsing):

```bash
# Comment out pandas in requirements.txt
sed -i '' 's/pandas==2.1.4/# pandas==2.1.4/' requirements.txt

# Install everything else
pip install -r requirements.txt

# Install pandas later if needed
```
