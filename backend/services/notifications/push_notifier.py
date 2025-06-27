"""Push notification implementation using Firebase Cloud Messaging."""

import json
from typing import Optional, Dict, Any

from core.config import get_settings
from core.exceptions import PushNotificationError, ConfigurationError
from .base import BaseNotifier, NotificationMessage, NotificationResult, NotificationType


class PushNotifier(BaseNotifier):
    """Push notifier using Firebase Cloud Messaging."""
    
    def __init__(self, settings=None):
        """
        Initialize the push notifier.
        
        Args:
            settings: Configuration settings
        """
        super().__init__(settings or get_settings())
        self._firebase_app = None
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate Firebase configuration."""
        if not self.settings.firebase_credentials_path:
            self.logger.warning("FIREBASE_CREDENTIALS_PATH not configured - push notifications will be disabled")
            self.disable()
            return
        
        # Check if credentials file exists
        import os
        if not os.path.exists(self.settings.firebase_credentials_path):
            self.logger.warning(f"Firebase credentials file not found: {self.settings.firebase_credentials_path}")
            self.disable()
            return
    
    def _get_firebase_app(self):
        """Get or create Firebase app instance."""
        if self._firebase_app is None:
            try:
                import firebase_admin
                from firebase_admin import credentials
                
                # Initialize Firebase app if not already done
                if not firebase_admin._apps:
                    cred = credentials.Certificate(self.settings.firebase_credentials_path)
                    self._firebase_app = firebase_admin.initialize_app(cred)
                else:
                    self._firebase_app = firebase_admin.get_app()
                    
            except ImportError:
                self.logger.error("Firebase Admin SDK not installed. Install with: pip install firebase-admin")
                self.disable()
                raise PushNotificationError("Firebase Admin SDK not installed")
            except Exception as e:
                self.logger.error(f"Error initializing Firebase app: {e}")
                self.disable()
                raise PushNotificationError(f"Firebase initialization error: {e}")
        
        return self._firebase_app
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """
        Send a push notification.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult indicating success or failure
        """
        try:
            from firebase_admin import messaging
            
            # Ensure Firebase is initialized
            self._get_firebase_app()
            
            # Create FCM message
            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    title=message.subject,
                    body=message.body
                ),
                data=message.metadata or {},
                token=message.recipient  # recipient should be FCM token
            )
            
            # Send message
            response = messaging.send(fcm_message)
            
            self.logger.info(f"Push notification sent successfully, message ID: {response}")
            
            return NotificationResult(
                success=True,
                message_id=response,
                provider_response={"message_id": response}
            )
            
        except Exception as e:
            # Handle Firebase-specific errors
            error_msg = f"Error sending push notification: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise PushNotificationError(error_msg)
    
    def send_multicast(self, message: NotificationMessage, tokens: list[str]) -> Dict[str, Any]:
        """
        Send push notification to multiple devices.
        
        Args:
            message: The notification message to send
            tokens: List of FCM tokens
            
        Returns:
            Dictionary with results for each token
        """
        try:
            from firebase_admin import messaging
            
            # Ensure Firebase is initialized
            self._get_firebase_app()
            
            # Create multicast message
            multicast_message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=message.subject,
                    body=message.body
                ),
                data=message.metadata or {},
                tokens=tokens
            )
            
            # Send multicast message
            response = messaging.send_multicast(multicast_message)
            
            self.logger.info(f"Multicast push notification sent: {response.success_count} successful, {response.failure_count} failed")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": [
                    {
                        "success": resp.success,
                        "message_id": resp.message_id if resp.success else None,
                        "error": str(resp.exception) if not resp.success else None
                    }
                    for resp in response.responses
                ]
            }
            
        except Exception as e:
            error_msg = f"Error sending multicast push notification: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise PushNotificationError(error_msg)
    
    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate FCM token format.
        
        Args:
            recipient: FCM token to validate
            
        Returns:
            True if valid FCM token format, False otherwise
        """
        if not recipient or not isinstance(recipient, str):
            return False
        
        # Basic FCM token validation
        # FCM tokens are typically long alphanumeric strings
        recipient = recipient.strip()
        
        # Should be at least 140 characters and contain only valid characters
        if len(recipient) < 140:
            return False
        
        # Should contain only alphanumeric characters, hyphens, underscores, and colons
        import re
        token_pattern = r'^[a-zA-Z0-9_:-]+$'
        return bool(re.match(token_pattern, recipient))
    
    def get_notification_type(self) -> NotificationType:
        """Return PUSH notification type."""
        return NotificationType.PUSH
    
    def send_train_delay_notification(
        self, 
        recipient: str, 
        station_name: str, 
        service_details: str,
        delay_minutes: int
    ) -> NotificationResult:
        """
        Send a train delay push notification.
        
        Args:
            recipient: FCM token to send to
            station_name: Name of the station
            service_details: Details of the delayed service
            delay_minutes: Number of minutes delayed
            
        Returns:
            NotificationResult
        """
        subject = f"Train Delay - {station_name}"
        body = f"{service_details} is delayed by {delay_minutes} minutes"
        
        message = NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.PUSH,
            metadata={
                "station_name": station_name,
                "delay_minutes": str(delay_minutes),
                "notification_type": "train_delay",
                "service_details": service_details
            }
        )
        
        return self.send_if_enabled(message)
    
    def send_service_disruption_notification(
        self, 
        recipient: str, 
        station_name: str, 
        disruption_details: str
    ) -> NotificationResult:
        """
        Send a service disruption push notification.
        
        Args:
            recipient: FCM token to send to
            station_name: Name of the station
            disruption_details: Details of the service disruption
            
        Returns:
            NotificationResult
        """
        subject = f"Service Disruption - {station_name}"
        body = disruption_details
        
        message = NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.PUSH,
            metadata={
                "station_name": station_name,
                "notification_type": "service_disruption",
                "disruption_details": disruption_details
            }
        )
        
        return self.send_if_enabled(message)
    
    def subscribe_to_topic(self, tokens: list[str], topic: str) -> Dict[str, Any]:
        """
        Subscribe FCM tokens to a topic.
        
        Args:
            tokens: List of FCM tokens
            topic: Topic name to subscribe to
            
        Returns:
            Dictionary with subscription results
        """
        try:
            from firebase_admin import messaging
            
            # Ensure Firebase is initialized
            self._get_firebase_app()
            
            response = messaging.subscribe_to_topic(tokens, topic)
            
            self.logger.info(f"Topic subscription: {response.success_count} successful, {response.failure_count} failed")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "errors": [str(error) for error in response.errors] if response.errors else []
            }
            
        except Exception as e:
            error_msg = f"Error subscribing to topic {topic}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise PushNotificationError(error_msg)
    
    def send_to_topic(self, message: NotificationMessage, topic: str) -> NotificationResult:
        """
        Send push notification to a topic.
        
        Args:
            message: The notification message to send
            topic: Topic to send to
            
        Returns:
            NotificationResult
        """
        try:
            from firebase_admin import messaging
            
            # Ensure Firebase is initialized
            self._get_firebase_app()
            
            # Create topic message
            topic_message = messaging.Message(
                notification=messaging.Notification(
                    title=message.subject,
                    body=message.body
                ),
                data=message.metadata or {},
                topic=topic
            )
            
            # Send message
            response = messaging.send(topic_message)
            
            self.logger.info(f"Topic push notification sent successfully to {topic}, message ID: {response}")
            
            return NotificationResult(
                success=True,
                message_id=response,
                provider_response={"message_id": response, "topic": topic}
            )
            
        except Exception as e:
            error_msg = f"Error sending push notification to topic {topic}: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise PushNotificationError(error_msg)
