# MOTHRA - Complete Beginner's Installation Guide

**For someone with zero experience - follow these exact steps!**

---

## Part 1: Install Required Software (One-Time Setup)

### Step 1: Install Python

**Windows:**
1. Go to https://www.python.org/downloads/
2. Click the big yellow button "Download Python 3.12.x"
3. Run the downloaded file
4. **IMPORTANT**: Check the box "Add Python to PATH" at the bottom
5. Click "Install Now"
6. Wait for installation to complete
7. Click "Close"

**Mac:**
1. Go to https://www.python.org/downloads/
2. Click "Download Python 3.12.x"
3. Open the downloaded .pkg file
4. Follow the installer, click "Continue" → "Install"
5. Enter your Mac password when asked
6. Click "Close" when done

**Verify Python is installed:**
1. Open Terminal (Mac) or Command Prompt (Windows)
   - **Mac**: Press `Cmd + Space`, type "Terminal", press Enter
   - **Windows**: Press `Windows Key`, type "cmd", press Enter
2. Type this and press Enter:
   ```
   python --version
   ```
3. You should see something like: `Python 3.12.0`
4. If you see an error, restart your computer and try again

---

### Step 2: Install Docker Desktop

**Windows:**
1. Go to https://www.docker.com/products/docker-desktop/
2. Click "Download for Windows"
3. Run the downloaded "Docker Desktop Installer.exe"
4. Follow the installer (use default settings)
5. Click "Ok" when it asks about WSL 2
6. Restart your computer when prompted
7. After restart, Docker Desktop will start automatically
8. Wait for the Docker icon in the taskbar to show "Docker Desktop is running"

**Mac:**
1. Go to https://www.docker.com/products/docker-desktop/
2. Click "Download for Mac" (choose Intel or Apple Silicon based on your Mac)
   - If unsure: Click Apple menu → "About This Mac" → look at "Chip" or "Processor"
   - M1/M2/M3 = Apple Silicon
   - Intel Core = Intel
3. Open the downloaded .dmg file
4. Drag Docker icon to Applications folder
5. Open Applications folder, double-click Docker
6. Click "Open" when it asks if you're sure
7. Enter your Mac password when asked
8. Wait for "Docker Desktop is running" at the top

**Verify Docker is installed:**
1. Open Terminal (Mac) or Command Prompt (Windows)
2. Type this and press Enter:
   ```
   docker --version
   ```
3. You should see something like: `Docker version 24.0.x`

---

### Step 3: Install Git

**Windows:**
1. Go to https://git-scm.com/download/win
2. Download will start automatically
3. Run the downloaded installer
4. Click "Next" through all screens (use default settings)
5. Click "Install"
6. Click "Finish"

**Mac:**
1. Open Terminal
2. Type this and press Enter:
   ```
   git --version
   ```
3. If Git is not installed, a popup will appear
4. Click "Install" and follow the prompts
5. Or go to https://git-scm.com/download/mac and download the installer

**Verify Git is installed:**
1. Open Terminal (Mac) or Command Prompt (Windows)
2. Type this and press Enter:
   ```
   git --version
   ```
3. You should see something like: `git version 2.x.x`

---

## Part 2: Download and Install MOTHRA

### Step 4: Open Terminal/Command Prompt

**Windows:**
1. Press `Windows Key`
2. Type: `cmd`
3. Press `Enter`
4. You should see a black window with text

**Mac:**
1. Press `Cmd + Space`
2. Type: `terminal`
3. Press `Enter`
4. You should see a window with text

---

### Step 5: Navigate to Where You Want to Install MOTHRA

Let's put it in your Documents folder:

**Windows - Type these commands one at a time:**
```cmd
cd Documents
```
Press Enter after typing this.

**Mac - Type these commands one at a time:**
```bash
cd Documents
```
Press Enter after typing this.

---

### Step 6: Download MOTHRA Code

**Copy and paste this command** (don't type it, copy/paste to avoid typos):

```bash
git clone https://github.com/nickgogerty/Mothra.git
```

Press Enter.

**What you'll see:**
```
Cloning into 'Mothra'...
remote: Enumerating objects: ...
remote: Counting objects: 100% ...
Receiving objects: 100% ...
```

This takes about 30 seconds. Wait for it to finish.

---

### Step 7: Enter the MOTHRA Folder

Type this command:
```bash
cd Mothra
```
Press Enter.

---

### Step 8: Switch to the Correct Branch

Copy and paste this command:
```bash
git checkout claude/mothra-carbon-database-011CUSGHTrH9htbUpPmK5pdM
```
Press Enter.

**What you'll see:**
```
Switched to branch 'claude/mothra-carbon-database-011CUSGHTrH9htbUpPmK5pdM'
```

---

### Step 9: Run the Automated Setup Script

**For Windows:**
Type this and press Enter:
```cmd
setup.bat
```

**For Mac:**
Type this and press Enter:
```bash
bash setup.sh
```

---

### Step 10: Wait for Installation to Complete

**What will happen (takes 5-10 minutes):**

You'll see messages like:
```
🦋 MOTHRA Setup Script
======================

[1/8] Checking prerequisites...
✅ Python 3.12 found
✅ Docker found
✅ Docker Compose found

[2/8] Creating Python virtual environment...
✅ Virtual environment created

[3/8] Installing Python dependencies...
This may take a few minutes (downloading sentence-transformers model)...
✅ Dependencies installed

[4/8] Creating environment configuration...
✅ .env file created

[5/8] Starting PostgreSQL with pgvector...
Waiting for PostgreSQL to be ready...
✅ PostgreSQL is running

[6/8] Initializing database schema...
✅ Database initialized with pgvector extension

[7/8] Discovering carbon data sources...
✅ Sources discovered and cataloged

[8/8] Testing local embeddings...
Loading sentence-transformers model...
✅ Embeddings working! Dimension: 384

============================================
🎉 MOTHRA Setup Complete!
============================================
```

**IMPORTANT:**
- Don't close the window while this is running
- It may look like it's stuck during step 3 - that's normal, be patient
- The first time downloads AI models (~500MB), so it takes longer

---

## Part 3: Verify Everything is Working

### Step 11: Check the Database

Copy and paste this command:

**Windows:**
```cmd
docker exec -it mothra-postgres psql -U mothra -c "SELECT count(*) FROM data_sources;"
```

**Mac:**
```bash
docker exec -it mothra-postgres psql -U mothra -c "SELECT count(*) FROM data_sources;"
```

**What you should see:**
```
 count
-------
    40
(1 row)
```

This means 40+ carbon data sources were discovered! ✅

---

## Part 4: Start Using MOTHRA

### Step 12: Activate the Python Environment

Every time you open a new terminal, you need to activate the environment first.

**Windows:**
```cmd
venv\Scripts\activate
```

**Mac:**
```bash
source venv/bin/activate
```

**What you'll see:**
Your command prompt will change to show `(venv)` at the beginning:
```
(venv) C:\Users\YourName\Documents\Mothra>
```

---

### Step 13: Start Crawling Data (Option 1 - Recommended for First Time)

Let's start with just discovering sources to make sure everything works:

Type this command:
```bash
python -m mothra.agents.survey.survey_agent
```

**What you'll see:**
```json
{"event": "survey_agent_starting", "level": "info", ...}
{"event": "catalog_loaded", "level": "info", ...}
{"event": "processing_category", "category": "government_apis", "count": 10, ...}
{"event": "source_validated", "url": "...", "status": 200, ...}
...
{"event": "survey_agent_complete", "sources_discovered": 40, ...}
```

This takes 2-3 minutes. ✅

---

### Step 14: Start Actual Crawling (Option 2 - Gets Real Data)

Now let's crawl some actual carbon data:

Type this command:
```bash
python -m mothra.agents.crawler.crawler_agent
```

**What you'll see:**
```json
{"event": "crawler_orchestrator_starting", ...}
{"event": "crawl_queue_populated", "count": 15, ...}
{"event": "crawl_started", "source_name": "EPA GHGRP", ...}
{"event": "crawl_completed", "source_name": "EPA GHGRP", "status": "completed", ...}
...
```

**This will:**
- Contact government APIs (EPA, DEFRA, etc.)
- Download carbon emissions data
- Store it in the database
- Takes 10-30 minutes depending on sources

**You can press `Ctrl+C` to stop it anytime.**

---

### Step 15: Run the Full Orchestrator (Option 3 - Everything Automatic)

This runs the complete workflow:

Type this command:
```bash
python -m mothra.orchestrator
```

**What it does:**
1. Discovers sources
2. Crawls data
3. Generates embeddings
4. Enables semantic search

**This takes 30-60 minutes.** Let it run in the background.

---

## Part 5: Exploring Your Data

### Step 16: View Data in the Database

See what sources were found:
```bash
docker exec -it mothra-postgres psql -U mothra -c "SELECT name, priority, status FROM data_sources LIMIT 10;"
```

See how many carbon entities:
```bash
docker exec -it mothra-postgres psql -U mothra -c "SELECT count(*) FROM carbon_entities;"
```

---

### Step 17: Test Semantic Search (After Embeddings are Generated)

Create a test file:

**Windows:**
```cmd
notepad test_search.py
```

**Mac:**
```bash
nano test_search.py
```

Copy and paste this code:
```python
import asyncio
from mothra.agents.embedding.vector_manager import VectorManager

async def search():
    manager = VectorManager()
    results = await manager.semantic_search(
        query="steel production emissions",
        limit=5
    )

    print("\n🔍 Search Results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['name']}")
        print(f"   Similarity: {result['similarity']:.2f}")
        print()

asyncio.run(search())
```

Save and run:
```bash
python test_search.py
```

---

## Troubleshooting

### Problem: "Python not found"
**Solution:**
1. Restart your computer
2. Reinstall Python, make sure to check "Add to PATH"
3. Try again

### Problem: "Docker not found" or "Docker daemon not running"
**Solution:**
1. Open Docker Desktop application
2. Wait for it to show "Docker Desktop is running"
3. Try again

### Problem: "Port 5432 already in use"
**Solution:**
1. You have another PostgreSQL running
2. Stop it, or change port in `docker-compose.yml`

### Problem: Script gets stuck at "Installing dependencies"
**Solution:**
1. Be patient, first install downloads ~500MB of AI models
2. Can take 10-20 minutes on slow internet
3. If truly stuck (30+ min), press `Ctrl+C` and run again

### Problem: "Permission denied" (Mac/Linux)
**Solution:**
```bash
chmod +x setup.sh
bash setup.sh
```

---

## Daily Usage (After Initial Setup)

Every time you want to use MOTHRA:

1. **Open Terminal/Command Prompt**
2. **Navigate to MOTHRA:**
   ```bash
   cd Documents/Mothra
   ```
3. **Activate environment:**
   - Windows: `venv\Scripts\activate`
   - Mac: `source venv/bin/activate`
4. **Run what you need:**
   - Crawl: `python -m mothra.agents.crawler.crawler_agent`
   - Orchestrator: `python -m mothra.orchestrator`

---

## Stopping MOTHRA

### Stop the crawler:
- Press `Ctrl+C` in the terminal

### Stop the database:
```bash
docker compose down
```

### Restart the database:
```bash
docker compose up -d postgres
```

---

## Getting Help

If you get stuck:

1. **Read the error message** - often tells you what's wrong
2. **Check INSTALL.md** - has more troubleshooting
3. **Google the error** - others have likely had same issue
4. **Ask for help** - create a GitHub issue with:
   - What step you're on
   - The exact error message
   - Your operating system

---

## What You've Built

Congratulations! You now have:

✅ A PostgreSQL database with vector search
✅ 100+ carbon data sources cataloged
✅ An AI-powered semantic search system
✅ Automated crawlers collecting emissions data
✅ A system that can store 100,000+ carbon entities

**You're ready to build the world's most comprehensive carbon database!** 🦋

---

## Next Steps to Learn More

1. Read `README.md` for architecture details
2. Read `QUICKSTART.md` for advanced usage
3. Explore the code in `mothra/` folder
4. Customize data sources in `mothra/data/sources_catalog.yaml`
5. Set up automated daily updates

**Welcome to MOTHRA!** 🚀
