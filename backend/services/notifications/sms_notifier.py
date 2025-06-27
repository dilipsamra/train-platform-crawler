"""SMS notification implementation using Twilio."""

import re
from typing import Optional

from core.config import get_settings
from core.exceptions import SMSNotificationError, ConfigurationError
from .base import BaseNotifier, NotificationMessage, NotificationResult, NotificationType


class SMSNotifier(BaseNotifier):
    """SMS notifier using Twilio API."""
    
    def __init__(self, settings=None):
        """
        Initialize the SMS notifier.
        
        Args:
            settings: Configuration settings
        """
        super().__init__(settings or get_settings())
        self._twilio_client = None
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate Twilio configuration."""
        if not self.settings.twilio_account_sid:
            self.logger.warning("TWILIO_ACCOUNT_SID not configured - SMS notifications will be disabled")
            self.disable()
            return
        
        if not self.settings.twilio_auth_token:
            self.logger.warning("TWILIO_AUTH_TOKEN not configured - SMS notifications will be disabled")
            self.disable()
            return
        
        if not self.settings.twilio_from_number:
            self.logger.warning("TWILIO_FROM_NUMBER not configured - SMS notifications will be disabled")
            self.disable()
            return
    
    def _get_twilio_client(self):
        """Get or create Twilio client instance."""
        if self._twilio_client is None:
            try:
                from twilio.rest import Client
                self._twilio_client = Client(
                    self.settings.twilio_account_sid,
                    self.settings.twilio_auth_token
                )
            except ImportError:
                self.logger.error("Twilio library not installed. Install with: pip install twilio")
                self.disable()
                raise SMSNotificationError("Twilio library not installed")
        
        return self._twilio_client
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """
        Send an SMS notification.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult indicating success or failure
        """
        try:
            client = self._get_twilio_client()
            
            # Combine subject and body for SMS (SMS doesn't have separate subject)
            sms_body = f"{message.subject}\n\n{message.body}" if message.subject else message.body
            
            # Truncate if too long (SMS has character limits)
            if len(sms_body) > 1600:  # Twilio's limit
                sms_body = sms_body[:1597] + "..."
            
            # Send SMS
            twilio_message = client.messages.create(
                body=sms_body,
                from_=self.settings.twilio_from_number,
                to=message.recipient
            )
            
            self.logger.info(f"SMS sent successfully to {message.recipient}, SID: {twilio_message.sid}")
            
            return NotificationResult(
                success=True,
                message_id=twilio_message.sid,
                provider_response={
                    "sid": twilio_message.sid,
                    "status": twilio_message.status,
                    "price": twilio_message.price,
                    "price_unit": twilio_message.price_unit
                }
            )
            
        except Exception as e:
            # Handle Twilio-specific errors
            if hasattr(e, 'code'):
                error_msg = f"Twilio error {e.code}: {e.msg}"
            else:
                error_msg = f"Unexpected error sending SMS: {e}"
            
            self.logger.error(error_msg, exc_info=True)
            raise SMSNotificationError(error_msg)
    
    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            recipient: Phone number to validate
            
        Returns:
            True if valid phone number format, False otherwise
        """
        if not recipient or not isinstance(recipient, str):
            return False
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', recipient.strip())
        
        # Basic phone number validation
        # Should start with + and have 10-15 digits
        phone_pattern = r'^\+\d{10,15}$'
        return bool(re.match(phone_pattern, cleaned))
    
    def get_notification_type(self) -> NotificationType:
        """Return SMS notification type."""
        return NotificationType.SMS
    
    def send_train_delay_notification(
        self, 
        recipient: str, 
        station_name: str, 
        service_details: str,
        delay_minutes: int
    ) -> NotificationResult:
        """
        Send a train delay notification SMS.
        
        Args:
            recipient: Phone number to send to
            station_name: Name of the station
            service_details: Details of the delayed service
            delay_minutes: Number of minutes delayed
            
        Returns:
            NotificationResult
        """
        subject = f"Train Delay - {station_name}"
        
        body = f"Service: {service_details}\nDelay: {delay_minutes} min\n\nTrain Platform Crawler"
        
        message = NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.SMS,
            metadata={
                "station_name": station_name,
                "delay_minutes": delay_minutes,
                "notification_type": "train_delay"
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
        Send a service disruption notification SMS.
        
        Args:
            recipient: Phone number to send to
            station_name: Name of the station
            disruption_details: Details of the service disruption
            
        Returns:
            NotificationResult
        """
        subject = f"Service Disruption - {station_name}"
        
        body = f"Disruption: {disruption_details}\n\nTrain Platform Crawler"
        
        message = NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.SMS,
            metadata={
                "station_name": station_name,
                "notification_type": "service_disruption"
            }
        )
        
        return self.send_if_enabled(message)
    
    def get_account_balance(self) -> Optional[str]:
        """
        Get Twilio account balance (useful for monitoring).
        
        Returns:
            Account balance as string, or None if unavailable
        """
        try:
            client = self._get_twilio_client()
            balance = client.api.accounts(self.settings.twilio_account_sid).balance.fetch()
            return f"{balance.balance} {balance.currency}"
        except Exception as e:
            self.logger.error(f"Error fetching Twilio account balance: {e}")
            return None
