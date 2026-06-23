"""Brief-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingBriefRulesError(RuleResolutionError):
    """Raised when the brief_rules section is missing or invalid."""

    code = "missing_brief_rules"

    def __init__(self) -> None:
        """Describe the missing brief_rules section."""
        super().__init__(
            "Missing or invalid brief_rules section in brief.yaml.",
            details={"section": "brief_rules"},
        )


class MissingBriefCriterionError(RuleResolutionError):
    """Raised when a required brief criterion is missing from the rules."""

    code = "missing_brief_criterion"

    def __init__(self, criterion_id: str) -> None:
        """Describe the missing brief criterion."""
        super().__init__(
            f"Missing required brief criterion: {criterion_id}",
            details={"criterion_id": criterion_id},
        )
