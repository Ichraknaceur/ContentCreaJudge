"""Application-specific exception hierarchy."""

from __future__ import annotations


class ContentCreaJudgeError(Exception):
    """Base exception for all application-specific errors."""

    status_code = 400
    code = "contentcreajudge_error"

    def __init__(
        self,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> None:
        """Store a stable application error message and optional details."""
        super().__init__(message)
        self.message = message
        self.details = details


class DomainError(ContentCreaJudgeError):
    """Base exception for business/domain errors."""

    code = "domain_error"


class DomainValidationError(DomainError):
    """Raised when user-provided domain input is invalid."""

    status_code = 422
    code = "domain_validation_error"


class RuleResolutionError(DomainError):
    """Raised when judge rules cannot be resolved from context or config."""

    status_code = 422
    code = "rule_resolution_error"


class ConfigurationError(ContentCreaJudgeError):
    """Raised when server-side configuration is invalid."""

    status_code = 500
    code = "configuration_error"


class InfrastructureError(ContentCreaJudgeError):
    """Raised when an external dependency or runtime service fails."""

    status_code = 500
    code = "infrastructure_error"
