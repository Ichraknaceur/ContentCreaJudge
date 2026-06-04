"""Tone-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingToneContextError(RuleResolutionError):
    """Raised when a required tone context field is missing."""

    code = "missing_tone_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by tone rules."""
        super().__init__(
            f"Missing tone context field: {field_name}",
            details={"field_name": field_name},
        )


class InvalidToneConfigurationError(RuleResolutionError):
    """Raised when the tone YAML configuration is invalid."""

    code = "invalid_tone_configuration"

    def __init__(self, message: str) -> None:
        """Describe the invalid tone configuration."""
        super().__init__(message)
