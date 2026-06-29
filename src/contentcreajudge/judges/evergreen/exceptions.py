"""Evergreen-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingEvergreenContextError(RuleResolutionError):
    """Raised when a required evergreen context field is missing."""

    code = "missing_evergreen_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by evergreen rules."""
        super().__init__(
            f"Missing evergreen context field: {field_name}",
            details={"field_name": field_name},
        )


class UnsupportedEvergreenValueError(RuleResolutionError):
    """Raised when an evergreen context value is not supported."""

    code = "unsupported_evergreen_value"

    def __init__(self, field_name: str, value: str, allowed: list[str]) -> None:
        """Describe the unsupported value and list the allowed ones."""
        super().__init__(
            f"Unsupported value for {field_name}: {value}",
            details={
                "field_name": field_name,
                "value": value,
                "allowed_values": allowed,
            },
        )
