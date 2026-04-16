"""FastAPI application factory for the ContentCreaJudge service."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version

from fastapi import FastAPI

from contentcreajudge.api.evaluations import router as evaluations_router
from contentcreajudge.api.health import router as health_router
from contentcreajudge.api.root import router as root_router
from contentcreajudge.api.judges.structure import router as structure_judge_router


def _resolve_package_version() -> str:
    """Return the installed package version or a safe development fallback."""
    try:
        return get_version("contentcreajudge")
    except PackageNotFoundError:
        return "0.0.0-dev"


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="ContentCreaJudge API",
        version=_resolve_package_version(),
        description=(
            "Rule-based API for evaluating editorial content compliance and "
            "quality checks."
        ),
    )
    application.include_router(root_router)
    application.include_router(health_router)
    application.include_router(evaluations_router)
    application.include_router(structure_judge_router)
    return application


app = create_app()
