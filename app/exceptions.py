"""
Custom Exceptions for FastAPI Application
"""

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Union, Any, Dict


class QueueAPIException(HTTPException):
    """Base exception for Queue API"""
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        headers: Dict[str, str] | None = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class DatabaseError(QueueAPIException):
    """Database operation failed"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=500, detail=detail)


class ValidationError(QueueAPIException):
    """Validation failed"""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(status_code=422, detail=detail)


class NotFoundError(HTTPException):
    """Resource not found"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(status_code=404, detail=detail)


class BadRequestError(HTTPException):
    """Bad request"""
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=400, detail=detail)


class ConflictError(QueueAPIException):
    """Resource conflict"""
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=409, detail=detail)


async def queue_exception_handler(request, exc: QueueAPIException):
    """Global exception handler for QueueAPIException"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )
