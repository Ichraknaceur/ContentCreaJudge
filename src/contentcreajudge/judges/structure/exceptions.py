"""Structure-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import RuleResolutionError


class MissingStructureContextError(RuleResolutionError):
    """Raised when a required structure context field is missing."""

    code = "missing_structure_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by structure rules."""
        super().__init__(
            f"Missing structure context field: {field_name}",
            details={"field_name": field_name},
        )
