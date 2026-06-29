"""SEO-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingSeoContextError(RuleResolutionError):
    """Raised when a required SEO context field is missing."""

    code = "missing_seo_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by SEO rules."""
        super().__init__(
            f"Missing SEO context field: {field_name}",
            details={"field_name": field_name},
        )


class UnsupportedSeoValueError(RuleResolutionError):
    """Raised when a SEO context value is not in the allowed set."""

    code = "unsupported_seo_value"

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
