"""Sources-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingSourcesContextError(RuleResolutionError):
    """Raised when a required sources context field is missing."""

    code = "missing_sources_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by sources rules."""
        super().__init__(
            f"Missing sources context field: {field_name}",
            details={"field_name": field_name},
        )


class UnsupportedSourcesValueError(RuleResolutionError):
    """Raised when a sources context value is not in the allowed set."""

    code = "unsupported_sources_value"

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
