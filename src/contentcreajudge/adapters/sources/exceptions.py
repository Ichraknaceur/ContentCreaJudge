"""Adapter-specific exceptions for the sources validator."""

from __future__ import annotations

from contentcreajudge.core.errors import ConfigurationError


class InvalidSourceAdapterConfigError(ConfigurationError):
    """Raised when the source URL validator receives invalid configuration."""

    code = "invalid_source_adapter_config"

    def __init__(self, field: str, reason: str) -> None:
        """Describe the invalid adapter configuration field."""
        super().__init__(
            f"Invalid source adapter configuration for '{field}': {reason}",
            details={"field": field, "reason": reason},
        )
