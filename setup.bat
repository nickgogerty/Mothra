@echo off
REM MOTHRA Setup Script for Windows
REM Run this script: setup.bat

echo ============================================
echo MOTHRA Setup Script - Windows
echo ============================================
echo.

REM Check Python
echo [1/8] Checking prerequisites...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    exit /b 1
)
echo Python found

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker not found. Please install Docker Desktop
    exit /b 1
)
echo Docker found

REM Create virtual environment
echo.
echo [2/8] Creating Python virtual environment...
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo [3/8] Installing Python dependencies...
echo This may take a few minutes...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo Dependencies installed

REM Create .env file
echo.
echo [4/8] Creating environment configuration...
if exist .env (
    echo .env already exists
) else (
    copy .env.example .env
    echo .env file created
)

REM Start Docker
echo.
echo [5/8] Starting PostgreSQL with pgvector...
docker compose up -d postgres
echo Waiting for PostgreSQL to be ready...
timeout /t 10 /nobreak >nul

echo PostgreSQL started

REM Initialize database
echo.
echo [6/8] Initializing database schema...
python -c "import asyncio; from mothra.db.session import init_db; asyncio.run(init_db())"
echo Database initialized

REM Discover sources
echo.
echo [7/8] Discovering carbon data sources...
python -m mothra.agents.survey.survey_agent
echo Sources discovered

REM Test embeddings
echo.
echo [8/8] Testing local embeddings...
python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); print('Embeddings working!')"

echo.
echo ============================================
echo MOTHRA Setup Complete!
echo ============================================
echo.
echo Next steps:
echo.
echo 1. Start crawling:
echo    python -m mothra.agents.crawler.crawler_agent
echo.
echo 2. Or run orchestrator:
echo    python -m mothra.orchestrator
echo.
echo To activate virtual environment:
echo    venv\Scripts\activate.bat
echo.
pause
