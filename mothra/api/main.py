"""
MOTHRA FastAPI Application
A beautiful, Swiss-minimal API for carbon emissions data
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mothra.api.routes import entities, sources, search, statistics

# Create FastAPI app with minimal, informative metadata
app = FastAPI(
    title="MOTHRA",
    description="Carbon Emissions Database API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(entities.router, prefix="/api/v1", tags=["Entities"])
app.include_router(sources.router, prefix="/api/v1", tags=["Sources"])
app.include_router(statistics.router, prefix="/api/v1", tags=["Statistics"])


@app.get("/")
async def root():
    """Root endpoint with system status."""
    return {
        "name": "MOTHRA",
        "version": "1.0.0",
        "status": "operational",
        "description": "Multi-agent carbon emissions database",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "mothra-api",
        },
    )
