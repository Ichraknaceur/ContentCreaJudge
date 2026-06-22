"""Editorial-style-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class InvalidEditorialStyleRulesError(RuleResolutionError):
    """Raised when editorial style rules are missing or invalid."""

    code = "invalid_editorial_style_rules"

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        """Describe an invalid editorial style rule configuration."""
        super().__init__(
            message,
            details=details or {},
        )


class MissingEditorialStyleCriterionError(RuleResolutionError):
    """Raised when a required editorial style criterion is missing."""

    code = "missing_editorial_style_criterion"

    def __init__(self, criterion_name: str) -> None:
        """Describe the missing criterion required by editorial style rules."""
        super().__init__(
            f"Missing editorial style criterion: {criterion_name}",
            details={"criterion_name": criterion_name},
        )


class InvalidEditorialStyleWeightError(RuleResolutionError):
    """Raised when editorial style criteria weights are invalid."""

    code = "invalid_editorial_style_weight"

    def __init__(self, total_weight: float) -> None:
        """Describe an invalid criteria weight sum."""
        super().__init__(
            "Editorial style criteria weights must sum to 1.0.",
            details={"total_weight": total_weight},
        )
