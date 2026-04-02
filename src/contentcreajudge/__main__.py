"""Package entrypoint for local API execution."""

import uvicorn


def main() -> None:
    """Run the local development API server."""
    uvicorn.run(
        "contentcreajudge.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )


if __name__ == "__main__":
    main()
