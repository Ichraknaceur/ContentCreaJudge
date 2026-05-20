"""Length-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingLengthContextError(RuleResolutionError):
    """Raised when a required length context field is missing."""

    code = "missing_length_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by length rules."""
        super().__init__(
            f"Missing length context field: {field_name}",
            details={"field_name": field_name},
        )


class UnsupportedLengthValueError(RuleResolutionError):
    """Raised when a length context value is not in the allowed set."""

    code = "unsupported_length_value"

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
