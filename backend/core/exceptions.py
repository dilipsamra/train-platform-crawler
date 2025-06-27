"""Custom exceptions and error handling for the train platform crawler application."""

from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import logging

from .logging import get_logger


class TrainPlatformCrawlerException(Exception):
    """Base exception for all train platform crawler errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ConfigurationError(TrainPlatformCrawlerException):
    """Raised when there's a configuration error."""
    pass


class APIClientError(TrainPlatformCrawlerException):
    """Base class for API client errors."""
    pass


class ExternalAPIError(APIClientError):
    """Raised when external API calls fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_body: Optional[str] = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message, details={"status_code": status_code, "response_body": response_body})


class APITimeoutError(APIClientError):
    """Raised when API requests timeout."""
    pass


class APIRateLimitError(APIClientError):
    """Raised when API rate limits are exceeded."""
    pass


class ValidationError(TrainPlatformCrawlerException):
    """Raised when data validation fails."""
    pass


class NotificationError(TrainPlatformCrawlerException):
    """Base class for notification errors."""
    pass


class EmailNotificationError(NotificationError):
    """Raised when email notifications fail."""
    pass


class SMSNotificationError(NotificationError):
    """Raised when SMS notifications fail."""
    pass


class PushNotificationError(NotificationError):
    """Raised when push notifications fail."""
    pass


class DataParsingError(TrainPlatformCrawlerException):
    """Raised when data parsing fails."""
    pass


class ServiceUnavailableError(TrainPlatformCrawlerException):
    """Raised when a service is temporarily unavailable."""
    pass


# HTTP Exception mappings
EXCEPTION_STATUS_CODES = {
    ConfigurationError: 500,
    ExternalAPIError: 502,
    APITimeoutError: 504,
    APIRateLimitError: 429,
    ValidationError: 400,
    NotificationError: 500,
    DataParsingError: 422,
    ServiceUnavailableError: 503,
    TrainPlatformCrawlerException: 500,
}


def create_http_exception(exc: TrainPlatformCrawlerException) -> HTTPException:
    """
    Convert a custom exception to an HTTP exception.
    
    Args:
        exc: The custom exception to convert
        
    Returns:
        HTTPException with appropriate status code and detail
    """
    status_code = EXCEPTION_STATUS_CODES.get(type(exc), 500)
    
    detail = {
        "error": exc.error_code,
        "message": exc.message,
        "details": exc.details
    }
    
    return HTTPException(status_code=status_code, detail=detail)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for the FastAPI application.
    
    Args:
        request: The FastAPI request object
        exc: The exception that was raised
        
    Returns:
        JSONResponse with error details
    """
    logger = get_logger("exception_handler")
    
    # Log the exception
    logger.error(f"Unhandled exception in {request.url}: {exc}", exc_info=True)
    
    # Handle custom exceptions
    if isinstance(exc, TrainPlatformCrawlerException):
        http_exc = create_http_exception(exc)
        return JSONResponse(
            status_code=http_exc.status_code,
            content=http_exc.detail
        )
    
    # Handle HTTP exceptions
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": "HTTPException", "message": exc.detail}
        )
    
    # Handle all other exceptions
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {}
        }
    )


def handle_api_error(response_status: int, response_text: str, url: str) -> None:
    """
    Handle API errors and raise appropriate exceptions.
    
    Args:
        response_status: HTTP status code from the API response
        response_text: Response body text
        url: The URL that was called
        
    Raises:
        Appropriate APIClientError subclass based on status code
    """
    if response_status == 429:
        raise APIRateLimitError(
            f"Rate limit exceeded for API call to {url}",
            details={"url": url, "status_code": response_status}
        )
    elif response_status == 504:
        raise APITimeoutError(
            f"API call to {url} timed out",
            details={"url": url, "status_code": response_status}
        )
    elif 400 <= response_status < 500:
        raise ExternalAPIError(
            f"Client error in API call to {url}: {response_text}",
            status_code=response_status,
            response_body=response_text
        )
    elif 500 <= response_status < 600:
        raise ExternalAPIError(
            f"Server error in API call to {url}: {response_text}",
            status_code=response_status,
            response_body=response_text
        )
    else:
        raise ExternalAPIError(
            f"Unexpected error in API call to {url}: {response_text}",
            status_code=response_status,
            response_body=response_text
        )


def log_and_raise(exception_class: type, message: str, **kwargs) -> None:
    """
    Log an error and raise the specified exception.
    
    Args:
        exception_class: The exception class to raise
        message: Error message
        **kwargs: Additional arguments to pass to the exception
    """
    logger = get_logger("error_handler")
    logger.error(message)
    raise exception_class(message, **kwargs)
