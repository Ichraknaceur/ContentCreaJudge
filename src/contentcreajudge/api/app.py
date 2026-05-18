"""FastAPI application factory for the ContentCreaJudge service."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_version
from typing import TYPE_CHECKING

from fastapi import FastAPI

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from contentcreajudge.api.error_handlers import register_error_handlers
from contentcreajudge.api.evaluations import router as evaluations_router
from contentcreajudge.api.health import router as health_router
from contentcreajudge.api.judges.sources import router as sources_judge_router
from contentcreajudge.api.judges.length import router as length_judge_router
from contentcreajudge.api.judges.seo import router as seo_judge_router
from contentcreajudge.api.judges.structure import router as structure_judge_router
from contentcreajudge.api.judges.typography import router as typography_judge_router
from contentcreajudge.api.root import router as root_router
from contentcreajudge.judges.seo.seo_judge import warmup_semantic_model

logger = logging.getLogger(__name__)


def _resolve_package_version() -> str:
    """Return the installed package version or a safe development fallback."""
    try:
        return get_version("contentcreajudge")
    except PackageNotFoundError:
        return "0.0.0-dev"


@asynccontextmanager
async def _lifespan(_application: FastAPI) -> AsyncGenerator[None]:
    logger.info("Warming up SEO semantic model...")
    warmup_semantic_model()
    logger.info("SEO semantic model ready.")
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="ContentCreaJudge API",
        version=_resolve_package_version(),
        description=(
            "Rule-based API for evaluating editorial content compliance and "
            "quality checks."
        ),
        lifespan=_lifespan,
    )
    register_error_handlers(application)
    application.include_router(root_router)
    application.include_router(health_router)
    application.include_router(evaluations_router)
    application.include_router(sources_judge_router)
    application.include_router(length_judge_router)
    application.include_router(seo_judge_router)
    application.include_router(typography_judge_router)
    application.include_router(structure_judge_router)
    return application


app = create_app()
