from typing import Any, Dict, Optional

class AppError(Exception):
    """Base exception for the application."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class WorkflowError(AppError):
    """Raised when a workflow operation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="WORKFLOW_ERROR", status_code=400, details=details)

class ResourceNotFoundError(AppError):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} with id '{resource_id}' not found",
            code="NOT_FOUND",
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
        )

class AuthenticationError(AppError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, code="AUTH_ERROR", status_code=401)

class PermissionError(AppError):
    """Raised when a user lacks permission."""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code="PERMISSION_DENIED", status_code=403)

class RateLimitError(AppError):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, code="RATE_LIMIT_EXCEEDED", status_code=429)

class ExternalServiceError(AppError):
    """Raised when an external dependency fails."""
    def __init__(self, service_name: str, original_error: str):
        super().__init__(
            f"Service {service_name} failed: {original_error}",
            code="DEPENDENCY_ERROR",
            status_code=502,
            details={"service": service_name}
        )
