"""Centralized logging configuration for the train platform crawler application."""

import logging
import logging.config
import sys
from typing import Optional

from .config import get_settings


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    logger_name: str = "train-platform-crawler"
) -> logging.Logger:
    """
    Set up centralized logging configuration.
    
    Args:
        log_level: Override the default log level from settings
        log_format: Override the default log format from settings
        logger_name: Name of the root logger
        
    Returns:
        Configured logger instance
    """
    settings = get_settings()
    
    # Use provided values or fall back to settings
    level = log_level or settings.log_level
    format_str = log_format or settings.log_format
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level),
        format=format_str,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Get the root logger for the application
    logger = logging.getLogger(logger_name)
    
    # Set specific log levels for external libraries to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name of the logger (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"train-platform-crawler.{name}")


class LoggerMixin:
    """Mixin class to add logging capability to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get a logger instance for this class."""
        return get_logger(self.__class__.__name__)


def log_function_call(func):
    """
    Decorator to log function calls with arguments and return values.
    Useful for debugging and monitoring.
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned: {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise
    
    return wrapper


def log_api_request(method: str, url: str, status_code: int, response_time: float):
    """
    Log API request details in a structured format.
    
    Args:
        method: HTTP method
        url: Request URL
        status_code: Response status code
        response_time: Response time in seconds
    """
    logger = get_logger("api_client")
    
    log_level = logging.INFO
    if status_code >= 400:
        log_level = logging.ERROR
    elif status_code >= 300:
        log_level = logging.WARNING
    
    logger.log(
        log_level,
        f"API Request: {method} {url} - Status: {status_code} - Time: {response_time:.3f}s"
    )


def log_notification_sent(notification_type: str, recipient: str, success: bool, error: Optional[str] = None):
    """
    Log notification sending attempts.
    
    Args:
        notification_type: Type of notification (email, sms, push)
        recipient: Recipient identifier
        success: Whether the notification was sent successfully
        error: Error message if sending failed
    """
    logger = get_logger("notifications")
    
    if success:
        logger.info(f"Notification sent successfully: {notification_type} to {recipient}")
    else:
        logger.error(f"Failed to send {notification_type} to {recipient}: {error}")
