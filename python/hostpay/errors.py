"""Exception hierarchy for the HostPay SDK."""
from __future__ import annotations

from typing import Optional


class HostPayError(Exception):
    """Base class for all SDK errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        detail: Optional[object] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class AuthenticationError(HostPayError):
    """Invalid or missing api-key / secret-key (401, 403)."""


class InvalidRequestError(HostPayError):
    """Bad request, not found, or validation error (400, 404, 422)."""


class RateLimitError(HostPayError):
    """Too many requests (429)."""


class APIError(HostPayError):
    """Server-side error (5xx)."""


class APIConnectionError(HostPayError):
    """Network problem reaching the API."""


class SignatureVerificationError(HostPayError):
    """A webhook signature could not be verified."""


def error_from_status(status_code: int, message: str, detail: object) -> HostPayError:
    if status_code in (401, 403):
        cls = AuthenticationError
    elif status_code == 429:
        cls = RateLimitError
    elif 400 <= status_code < 500:
        cls = InvalidRequestError
    else:
        cls = APIError
    return cls(message, status_code=status_code, detail=detail)
