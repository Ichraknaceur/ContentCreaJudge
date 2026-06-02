"""Persona-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingPersonaContextError(RuleResolutionError):
    """Raised when a required persona context field is missing."""

    code = "missing_persona_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by persona rules."""
        super().__init__(
            f"Missing persona context field: {field_name}",
            details={"field_name": field_name},
        )


class UnsupportedPersonaValueError(RuleResolutionError):
    """Raised when a persona context value is not in the allowed set."""

    code = "unsupported_persona_value"

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


class InvalidPersonaRulesError(RuleResolutionError):
    """Raised when the persona YAML rules are incomplete or invalid."""

    code = "invalid_persona_rules"

    def __init__(self, reason: str) -> None:
        """Describe why the persona rules configuration is invalid."""
        super().__init__(
            f"Invalid persona rules configuration: {reason}",
            details={"reason": reason},
        )
