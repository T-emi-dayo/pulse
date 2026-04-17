#!/usr/bin/env python3
"""
CLI entry point for the Agentic System
"""
import argparse
import uvicorn
from src.config.settings import settings
from src.utils.logging import setup_logging

def main():
    parser = argparse.ArgumentParser(description="Agentic System CLI")
    parser.add_argument("--host", default=settings.host, help="Host to bind to")
    parser.add_argument("--port", type=int, default=settings.port, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Run the FastAPI app
    uvicorn.run(
        "src.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload or settings.debug
    )

if __name__ == "__main__":
    main()
