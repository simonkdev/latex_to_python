"""FastAPI application for LaTeX to Python conversion, compatible with Vercel and local execution."""

from __future__ import annotations

import argparse
import os
import uvicorn
from fastapi import FastAPI
from mangum import Mangum
from api.main import app

# Vercel serverless handler
handler = Mangum(app)

def main() -> None:
    """Run the app locally using uvicorn."""
    parser = argparse.ArgumentParser(description="Run the local translator app.")
    parser.add_argument("--host", default="0.0.0.0" if os.getenv("VERCEL_ENV") else "127.0.0.1")
    parser.add_argument("--port", default=int(os.getenv("PORT", 8000)), type=int)
    parser.add_argument("--no-reload", action="store_true")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}"
    print(f"Frontend: {base_url}/")
    print(f"API:      {base_url}/api/v1/convert")
    print(f"Health:   {base_url}/health")

    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
    )

if __name__ == "__main__":
    main()
