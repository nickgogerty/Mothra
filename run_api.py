#!/usr/bin/env python3
"""
MOTHRA API Server Startup Script
Starts the FastAPI backend server
"""

import uvicorn

if __name__ == "__main__":
    print("Starting MOTHRA API server...")
    print("API will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/api/docs")
    print("\nPress CTRL+C to stop the server\n")

    uvicorn.run(
        "mothra.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
