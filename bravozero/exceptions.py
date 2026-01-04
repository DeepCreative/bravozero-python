"""
Bravo Zero SDK Exceptions
"""

from typing import Any, Optional


class BravoZeroError(Exception):
    """Base exception for Bravo Zero SDK."""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AuthenticationError(BravoZeroError):
    """Authentication or attestation failed."""
    pass


class RateLimitError(BravoZeroError):
    """Rate limit exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: int = 60,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.retry_after = retry_after


class ConstitutionDeniedError(BravoZeroError):
    """Constitution Agent denied the request."""
    
    def __init__(
        self,
        message: str,
        result: Any = None,
        details: Optional[dict] = None,
    ):
        super().__init__(message, details)
        self.result = result
        self.reasoning = message


class MemoryError(BravoZeroError):
    """Memory Service error."""
    pass


class BridgeError(BravoZeroError):
    """Forge Bridge error."""
    pass


class NotFoundError(BravoZeroError):
    """Resource not found."""
    pass


class ValidationError(BravoZeroError):
    """Request validation failed."""
    pass
