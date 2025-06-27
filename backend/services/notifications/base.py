"""Base notification interface and common functionality."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from core.logging import LoggerMixin


class NotificationType(Enum):
    """Types of notifications supported."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class NotificationPriority(Enum):
    """Priority levels for notifications."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationMessage:
    """Data class representing a notification message."""
    recipient: str
    subject: str
    body: str
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class NotificationResult:
    """Result of a notification sending attempt."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    provider_response: Optional[Dict[str, Any]] = None


class BaseNotifier(ABC, LoggerMixin):
    """Abstract base class for all notification providers."""
    
    def __init__(self, settings=None):
        """
        Initialize the notifier.
        
        Args:
            settings: Configuration settings
        """
        self.settings = settings
        self.enabled = True
    
    @abstractmethod
    def send(self, message: NotificationMessage) -> NotificationResult:
        """
        Send a notification message.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult indicating success or failure
        """
        pass
    
    @abstractmethod
    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate that a recipient address/number is valid for this notifier.
        
        Args:
            recipient: The recipient to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_notification_type(self) -> NotificationType:
        """
        Get the notification type this notifier handles.
        
        Returns:
            NotificationType enum value
        """
        pass
    
    def is_enabled(self) -> bool:
        """
        Check if this notifier is enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        return self.enabled
    
    def disable(self):
        """Disable this notifier."""
        self.enabled = False
        self.logger.info(f"{self.__class__.__name__} disabled")
    
    def enable(self):
        """Enable this notifier."""
        self.enabled = True
        self.logger.info(f"{self.__class__.__name__} enabled")
    
    def send_if_enabled(self, message: NotificationMessage) -> NotificationResult:
        """
        Send a notification only if the notifier is enabled.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult
        """
        if not self.is_enabled():
            self.logger.debug(f"Skipping {self.get_notification_type().value} notification - notifier disabled")
            return NotificationResult(
                success=False,
                error="Notifier is disabled"
            )
        
        if not self.validate_recipient(message.recipient):
            self.logger.error(f"Invalid recipient for {self.get_notification_type().value}: {message.recipient}")
            return NotificationResult(
                success=False,
                error=f"Invalid recipient: {message.recipient}"
            )
        
        try:
            return self.send(message)
        except Exception as e:
            self.logger.error(f"Error sending {self.get_notification_type().value} notification: {e}", exc_info=True)
            return NotificationResult(
                success=False,
                error=str(e)
            )


class MockNotifier(BaseNotifier):
    """Mock notifier for testing purposes."""
    
    def __init__(self, notification_type: NotificationType, should_fail: bool = False):
        """
        Initialize mock notifier.
        
        Args:
            notification_type: Type of notification this mock handles
            should_fail: Whether to simulate failures
        """
        super().__init__()
        self.notification_type = notification_type
        self.should_fail = should_fail
        self.sent_messages: List[NotificationMessage] = []
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """Mock send implementation."""
        if self.should_fail:
            return NotificationResult(
                success=False,
                error="Mock failure"
            )
        
        self.sent_messages.append(message)
        return NotificationResult(
            success=True,
            message_id=f"mock_{len(self.sent_messages)}"
        )
    
    def validate_recipient(self, recipient: str) -> bool:
        """Mock validation - always returns True unless empty."""
        return bool(recipient.strip())
    
    def get_notification_type(self) -> NotificationType:
        """Return the configured notification type."""
        return self.notification_type
    
    def clear_sent_messages(self):
        """Clear the list of sent messages (useful for testing)."""
        self.sent_messages.clear()
