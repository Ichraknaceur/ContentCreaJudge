"""Funnel-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingFunnelContextError(RuleResolutionError):
    """Raised when a required funnel context field is missing."""

    code = "missing_funnel_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by funnel rules."""
        super().__init__(
            f"Missing funnel context field: {field_name}",
            details={"field_name": field_name},
        )


class UnsupportedFunnelValueError(RuleResolutionError):
    """Raised when a funnel context value is not in the allowed set."""

    code = "unsupported_funnel_value"

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


class InvalidFunnelRulesError(RuleResolutionError):
    """Raised when the funnel rules configuration is invalid."""

    code = "invalid_funnel_rules"

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        """Describe an invalid funnel rule configuration."""
        super().__init__(
            message,
            details=details or {},
        )
