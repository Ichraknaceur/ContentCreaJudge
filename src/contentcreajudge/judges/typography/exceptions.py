"""Typography-specific application exceptions."""

from __future__ import annotations

from contentcreajudge.core.errors import DomainValidationError, RuleResolutionError


class TypographyError(DomainValidationError):
    """Base exception for typography judge errors."""

    code = "typography_error"


class MissingTypographyContextError(RuleResolutionError):
    """Raised when required typography context is missing."""

    code = "missing_typography_context"

    def __init__(self, field_name: str) -> None:
        """Describe the missing context field required by typography rules."""
        super().__init__(
            f"Missing typography context field: {field_name}",
            details={"field_name": field_name},
        )


class UnsupportedTypographyLocaleError(RuleResolutionError):
    """Raised when the provided typography locale is not supported."""

    code = "unsupported_typography_locale"

    def __init__(self, locale: str, supported_locales: list[str]) -> None:
        """Describe the unsupported locale and list the allowed values."""
        super().__init__(
            f"Unsupported locale for typography evaluation: {locale}",
            details={
                "locale": locale,
                "supported_locales": supported_locales,
            },
        )
