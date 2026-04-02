"""Root endpoint for API discovery."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

from fastapi import APIRouter

router = APIRouter(tags=["root"])


def _resolve_package_version() -> str:
    """Return the installed package version or a safe development fallback."""
    try:
        return get_version("contentcreajudge")
    except PackageNotFoundError:
        return "0.0.0-dev"


@router.get("/")
def get_root() -> dict[str, object]:
    """Return a small discovery payload for the API root."""
    return {
        "service": "contentcreajudge",
        "status": "ok",
        "version": _resolve_package_version(),
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "evaluations": "/api/v1/evaluations",
        },
    }
