"""Custom exceptions for SWB client."""

from typing import Any


class SWBError(Exception):
    """Base exception for all SWB client errors."""

    pass


class ConfigurationError(SWBError):
    """Invalid configuration or parameters."""

    pass


class ValidationError(SWBError):
    """Invalid input parameters."""

    pass


class APIError(SWBError):
    """Error from the SRU API."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize API error.

        Args:
            message: Error message
            status_code: HTTP status code if applicable
        """
        super().__init__(message)
        self.status_code = status_code


class ParseError(SWBError):
    """Error parsing API response."""

    def __init__(self, message: str, xml_snippet: str | None = None) -> None:
        """Initialize parse error.

        Args:
            message: Error message
            xml_snippet: First part of XML that failed to parse
        """
        super().__init__(message)
        self.xml_snippet = xml_snippet


class NetworkError(SWBError):
    """Network or connection error."""

    pass


class AuthenticationError(APIError):
    """Authentication failed (403)."""

    pass


class RateLimitError(APIError):
    """Rate limit exceeded (429)."""

    pass


class ServerError(APIError):
    """Server error (5xx)."""

    pass


def format_error_message(
    error_type: str,
    details: str,
    suggestion: str | None = None,
    context: dict[str, Any] | None = None,
) -> str:
    """Format error message consistently.

    Args:
        error_type: Type of error (e.g., "XML Parsing Error")
        details: Detailed description
        suggestion: Optional suggestion for fixing
        context: Optional context information

    Returns:
        Formatted error message

    Example:
        >>> format_error_message(
        ...     error_type="Invalid Parameter",
        ...     details="Value must be positive",
        ...     suggestion="Use a value greater than 0",
        ...     context={"parameter": "maximum_records", "value": -1}
        ... )
        'Invalid Parameter: Value must be positive\\nContext:\\n  parameter: maximum_records\\n  value: -1\\nSuggestion: Use a value greater than 0'
    """
    parts = [f"{error_type}: {details}"]

    if context:
        parts.append("Context:")
        for key, value in context.items():
            parts.append(f"  {key}: {value}")

    if suggestion:
        parts.append(f"Suggestion: {suggestion}")

    return "\n".join(parts)
