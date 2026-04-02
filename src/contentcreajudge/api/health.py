"""Health endpoints for the ContentCreaJudge API."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

from fastapi import APIRouter

router = APIRouter(tags=["health"])


def _resolve_package_version() -> str:
    """Return the installed package version or a safe development fallback."""
    try:
        return get_version("contentcreajudge")
    except PackageNotFoundError:
        return "0.0.0-dev"


@router.get("/health")
def get_health() -> dict[str, str]:
    """Return a minimal service health payload."""
    return {
        "status": "ok",
        "service": "contentcreajudge",
        "version": _resolve_package_version(),
    }
