"""Main notification service that orchestrates different notification types."""

from typing import List, Dict, Any, Optional
from enum import Enum

from core.config import get_settings
from core.logging import get_logger, log_notification_sent, LoggerMixin
from .base import (
    BaseNotifier, 
    NotificationMessage, 
    NotificationResult, 
    NotificationType,
    NotificationPriority,
    MockNotifier
)
from .email_notifier import EmailNotifier
from .sms_notifier import SMSNotifier
from .push_notifier import PushNotifier


class NotificationService(LoggerMixin):
    """Main service for managing and sending notifications."""
    
    def __init__(self, settings=None, use_mock_notifiers: bool = False):
        """
        Initialize the notification service.
        
        Args:
            settings: Configuration settings
            use_mock_notifiers: Whether to use mock notifiers (for testing)
        """
        self.settings = settings or get_settings()
        self.notifiers: Dict[NotificationType, BaseNotifier] = {}
        
        if use_mock_notifiers:
            self._setup_mock_notifiers()
        else:
            self._setup_notifiers()
    
    def _setup_notifiers(self):
        """Set up real notification providers."""
        try:
            self.notifiers[NotificationType.EMAIL] = EmailNotifier(self.settings)
        except Exception as e:
            self.logger.error(f"Failed to initialize email notifier: {e}")
            self.notifiers[NotificationType.EMAIL] = MockNotifier(NotificationType.EMAIL, should_fail=True)
        
        try:
            self.notifiers[NotificationType.SMS] = SMSNotifier(self.settings)
        except Exception as e:
            self.logger.error(f"Failed to initialize SMS notifier: {e}")
            self.notifiers[NotificationType.SMS] = MockNotifier(NotificationType.SMS, should_fail=True)
        
        try:
            self.notifiers[NotificationType.PUSH] = PushNotifier(self.settings)
        except Exception as e:
            self.logger.error(f"Failed to initialize push notifier: {e}")
            self.notifiers[NotificationType.PUSH] = MockNotifier(NotificationType.PUSH, should_fail=True)
    
    def _setup_mock_notifiers(self):
        """Set up mock notifiers for testing."""
        self.notifiers[NotificationType.EMAIL] = MockNotifier(NotificationType.EMAIL)
        self.notifiers[NotificationType.SMS] = MockNotifier(NotificationType.SMS)
        self.notifiers[NotificationType.PUSH] = MockNotifier(NotificationType.PUSH)
    
    def send_notification(
        self, 
        notification_type: NotificationType, 
        message: NotificationMessage
    ) -> NotificationResult:
        """
        Send a single notification.
        
        Args:
            notification_type: Type of notification to send
            message: The notification message
            
        Returns:
            NotificationResult indicating success or failure
        """
        notifier = self.notifiers.get(notification_type)
        if not notifier:
            error_msg = f"No notifier available for type: {notification_type.value}"
            self.logger.error(error_msg)
            return NotificationResult(success=False, error=error_msg)
        
        try:
            result = notifier.send_if_enabled(message)
            
            # Log the notification attempt
            log_notification_sent(
                notification_type.value,
                message.recipient,
                result.success,
                result.error
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Error sending {notification_type.value} notification: {e}"
            self.logger.error(error_msg, exc_info=True)
            
            log_notification_sent(
                notification_type.value,
                message.recipient,
                False,
                error_msg
            )
            
            return NotificationResult(success=False, error=error_msg)
    
    def send_multi_channel_notification(
        self, 
        message: NotificationMessage,
        channels: List[NotificationType],
        recipients: Dict[NotificationType, str]
    ) -> Dict[NotificationType, NotificationResult]:
        """
        Send the same message across multiple notification channels.
        
        Args:
            message: Base notification message
            channels: List of notification types to use
            recipients: Mapping of notification type to recipient
            
        Returns:
            Dictionary mapping notification type to result
        """
        results = {}
        
        for channel in channels:
            if channel not in recipients:
                self.logger.warning(f"No recipient specified for {channel.value}")
                results[channel] = NotificationResult(
                    success=False, 
                    error="No recipient specified"
                )
                continue
            
            # Create a copy of the message with the appropriate recipient
            channel_message = NotificationMessage(
                recipient=recipients[channel],
                subject=message.subject,
                body=message.body,
                notification_type=channel,
                priority=message.priority,
                metadata=message.metadata
            )
            
            results[channel] = self.send_notification(channel, channel_message)
        
        return results
    
    def send_train_delay_alert(
        self,
        station_name: str,
        service_details: str,
        delay_minutes: int,
        recipients: Dict[NotificationType, str],
        priority: NotificationPriority = NotificationPriority.HIGH
    ) -> Dict[NotificationType, NotificationResult]:
        """
        Send train delay alerts across multiple channels.
        
        Args:
            station_name: Name of the station
            service_details: Details of the delayed service
            delay_minutes: Number of minutes delayed
            recipients: Mapping of notification type to recipient
            priority: Priority level of the notification
            
        Returns:
            Dictionary mapping notification type to result
        """
        results = {}
        
        for notification_type, recipient in recipients.items():
            notifier = self.notifiers.get(notification_type)
            if not notifier:
                results[notification_type] = NotificationResult(
                    success=False,
                    error=f"No notifier available for {notification_type.value}"
                )
                continue
            
            # Use specialized methods if available
            if hasattr(notifier, 'send_train_delay_notification'):
                try:
                    result = notifier.send_train_delay_notification(
                        recipient, station_name, service_details, delay_minutes
                    )
                    results[notification_type] = result
                except Exception as e:
                    results[notification_type] = NotificationResult(
                        success=False,
                        error=str(e)
                    )
            else:
                # Fallback to generic notification
                subject = f"Train Delay - {station_name}"
                body = f"{service_details} is delayed by {delay_minutes} minutes"
                
                message = NotificationMessage(
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    notification_type=notification_type,
                    priority=priority,
                    metadata={
                        "station_name": station_name,
                        "delay_minutes": delay_minutes,
                        "notification_type": "train_delay"
                    }
                )
                
                results[notification_type] = self.send_notification(notification_type, message)
        
        return results
    
    def send_service_disruption_alert(
        self,
        station_name: str,
        disruption_details: str,
        recipients: Dict[NotificationType, str],
        priority: NotificationPriority = NotificationPriority.URGENT
    ) -> Dict[NotificationType, NotificationResult]:
        """
        Send service disruption alerts across multiple channels.
        
        Args:
            station_name: Name of the station
            disruption_details: Details of the service disruption
            recipients: Mapping of notification type to recipient
            priority: Priority level of the notification
            
        Returns:
            Dictionary mapping notification type to result
        """
        results = {}
        
        for notification_type, recipient in recipients.items():
            notifier = self.notifiers.get(notification_type)
            if not notifier:
                results[notification_type] = NotificationResult(
                    success=False,
                    error=f"No notifier available for {notification_type.value}"
                )
                continue
            
            # Use specialized methods if available
            if hasattr(notifier, 'send_service_disruption_notification'):
                try:
                    result = notifier.send_service_disruption_notification(
                        recipient, station_name, disruption_details
                    )
                    results[notification_type] = result
                except Exception as e:
                    results[notification_type] = NotificationResult(
                        success=False,
                        error=str(e)
                    )
            else:
                # Fallback to generic notification
                subject = f"Service Disruption - {station_name}"
                body = disruption_details
                
                message = NotificationMessage(
                    recipient=recipient,
                    subject=subject,
                    body=body,
                    notification_type=notification_type,
                    priority=priority,
                    metadata={
                        "station_name": station_name,
                        "notification_type": "service_disruption"
                    }
                )
                
                results[notification_type] = self.send_notification(notification_type, message)
        
        return results
    
    def get_notifier_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get the status of all notifiers.
        
        Returns:
            Dictionary with status information for each notifier
        """
        status = {}
        
        for notification_type, notifier in self.notifiers.items():
            status[notification_type.value] = {
                "enabled": notifier.is_enabled(),
                "type": notifier.__class__.__name__,
                "notification_type": notification_type.value
            }
        
        return status
    
    def enable_notifier(self, notification_type: NotificationType):
        """Enable a specific notifier."""
        notifier = self.notifiers.get(notification_type)
        if notifier:
            notifier.enable()
            self.logger.info(f"Enabled {notification_type.value} notifier")
        else:
            self.logger.warning(f"No notifier found for type: {notification_type.value}")
    
    def disable_notifier(self, notification_type: NotificationType):
        """Disable a specific notifier."""
        notifier = self.notifiers.get(notification_type)
        if notifier:
            notifier.disable()
            self.logger.info(f"Disabled {notification_type.value} notifier")
        else:
            self.logger.warning(f"No notifier found for type: {notification_type.value}")


# Global notification service instance
_notification_service = None


def get_notification_service(use_mock_notifiers: bool = False) -> NotificationService:
    """
    Get a singleton instance of the notification service.
    
    Args:
        use_mock_notifiers: Whether to use mock notifiers (for testing)
        
    Returns:
        NotificationService instance
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(use_mock_notifiers=use_mock_notifiers)
    return _notification_service


def set_notification_service(service: NotificationService):
    """
    Set the global notification service instance (useful for testing).
    
    Args:
        service: NotificationService instance to use
    """
    global _notification_service
    _notification_service = service
