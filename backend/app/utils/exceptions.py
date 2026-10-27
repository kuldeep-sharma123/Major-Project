"""
Custom exception hierarchy for the AI Autonomous Testing Agent.
All exceptions map to specific HTTP status codes.
"""
from __future__ import annotations

from typing import Any, Dict, Optional


class AppException(Exception):
    """
    Base application exception.

    Attributes:
        message:    Human-readable error message.
        status_code: HTTP status code to return to the client.
        detail:     Optional structured detail dict (serialised to JSON).
        log_level:  Loguru log level string.
    """

    status_code: int = 500
    log_level: str = "error"

    def __init__(
        self,
        message: str,
        detail: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "detail": self.detail,
        }


# ── Discovery ──────────────────────────────────────────────────────────────

class DiscoveryException(AppException):
    """Raised when the crawler / discovery pipeline fails."""

    status_code = 502

    def __init__(self, message: str, url: str = "", **kwargs: Any) -> None:
        super().__init__(message, detail={"url": url}, **kwargs)


class CrawlTimeoutException(DiscoveryException):
    """Raised when page crawl exceeds configured timeout."""

    status_code = 504


# ── Test generation ────────────────────────────────────────────────────────

class TestGenerationException(AppException):
    """Raised when the AI test-case generation pipeline fails."""

    status_code = 500

    def __init__(self, message: str, page_url: str = "", **kwargs: Any) -> None:
        super().__init__(message, detail={"page_url": page_url}, **kwargs)


class AIProviderException(AppException):
    """Raised on AI API errors (rate limit, bad response, etc.)."""

    status_code = 503

    def __init__(self, message: str, provider: str = "", **kwargs: Any) -> None:
        super().__init__(message, detail={"provider": provider}, **kwargs)


# ── Execution ─────────────────────────────────────────────────────────────

class ExecutionException(AppException):
    """Raised when Playwright test execution encounters a fatal error."""

    status_code = 500

    def __init__(self, message: str, test_name: str = "", **kwargs: Any) -> None:
        super().__init__(message, detail={"test_name": test_name}, **kwargs)


class ScriptGenerationException(AppException):
    """Raised when Playwright script code generation fails."""

    status_code = 500


# ── Reporting ─────────────────────────────────────────────────────────────

class ReportException(AppException):
    """Raised when report generation fails."""

    status_code = 500

    def __init__(self, message: str, format_: str = "", **kwargs: Any) -> None:
        super().__init__(message, detail={"format": format_}, **kwargs)


# ── Resource ──────────────────────────────────────────────────────────────

class NotFoundException(AppException):
    """Resource not found (404)."""

    status_code = 404
    log_level = "warning"

    def __init__(self, resource: str, resource_id: Any = "") -> None:
        super().__init__(
            f"{resource} not found.",
            detail={"resource": resource, "id": str(resource_id)},
        )


class ConflictException(AppException):
    """Resource conflict (409)."""

    status_code = 409
    log_level = "warning"


class ValidationException(AppException):
    """Request validation failed (422)."""

    status_code = 422
    log_level = "warning"


class StorageException(AppException):
    """File storage read/write error."""

    status_code = 500
