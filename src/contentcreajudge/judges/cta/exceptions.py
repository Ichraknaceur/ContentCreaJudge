"""CTA-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingCTAContextError(RuleResolutionError):
    """Raised when a required CTA context field is missing."""

    code = "missing_cta_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by CTA rules."""
        super().__init__(
            f"Missing CTA context field: {field_name}",
            details={"field_name": field_name},
        )


class UnsupportedCTAValueError(RuleResolutionError):
    """Raised when a CTA context value is not in the allowed set."""

    code = "unsupported_cta_value"

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
