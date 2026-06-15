"""Start the local API and browser frontend."""

from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local translator app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
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
