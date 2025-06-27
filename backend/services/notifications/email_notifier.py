"""Email notification implementation using SMTP."""

import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from core.config import get_settings
from core.exceptions import EmailNotificationError, ConfigurationError
from .base import BaseNotifier, NotificationMessage, NotificationResult, NotificationType


class EmailNotifier(BaseNotifier):
    """Email notifier using SMTP."""
    
    def __init__(self, settings=None):
        """
        Initialize the email notifier.
        
        Args:
            settings: Configuration settings
        """
        super().__init__(settings or get_settings())
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate email configuration."""
        if not self.settings.smtp_host:
            self.logger.warning("SMTP_HOST not configured - email notifications will be disabled")
            self.disable()
            return
        
        if not self.settings.smtp_username:
            self.logger.warning("SMTP_USERNAME not configured - email notifications will be disabled")
            self.disable()
            return
        
        if not self.settings.smtp_password:
            self.logger.warning("SMTP_PASSWORD not configured - email notifications will be disabled")
            self.disable()
            return
    
    def send(self, message: NotificationMessage) -> NotificationResult:
        """
        Send an email notification.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult indicating success or failure
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.settings.smtp_username
            msg['To'] = message.recipient
            msg['Subject'] = message.subject
            
            # Add body
            msg.attach(MIMEText(message.body, 'plain'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as server:
                if self.settings.smtp_use_tls:
                    server.starttls()
                
                server.login(self.settings.smtp_username, self.settings.smtp_password)
                
                # Send email
                text = msg.as_string()
                server.sendmail(self.settings.smtp_username, message.recipient, text)
                
                self.logger.info(f"Email sent successfully to {message.recipient}")
                
                return NotificationResult(
                    success=True,
                    message_id=f"email_{hash(message.recipient + message.subject)}"
                )
                
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {e}"
            self.logger.error(error_msg)
            raise EmailNotificationError(error_msg)
            
        except smtplib.SMTPRecipientsRefused as e:
            error_msg = f"SMTP recipients refused: {e}"
            self.logger.error(error_msg)
            raise EmailNotificationError(error_msg)
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {e}"
            self.logger.error(error_msg)
            raise EmailNotificationError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error sending email: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise EmailNotificationError(error_msg)
    
    def validate_recipient(self, recipient: str) -> bool:
        """
        Validate email address format.
        
        Args:
            recipient: Email address to validate
            
        Returns:
            True if valid email format, False otherwise
        """
        if not recipient or not isinstance(recipient, str):
            return False
        
        # Basic email validation regex
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, recipient.strip()))
    
    def get_notification_type(self) -> NotificationType:
        """Return EMAIL notification type."""
        return NotificationType.EMAIL
    
    def send_train_delay_notification(
        self, 
        recipient: str, 
        station_name: str, 
        service_details: str,
        delay_minutes: int
    ) -> NotificationResult:
        """
        Send a train delay notification email.
        
        Args:
            recipient: Email address to send to
            station_name: Name of the station
            service_details: Details of the delayed service
            delay_minutes: Number of minutes delayed
            
        Returns:
            NotificationResult
        """
        subject = f"Train Delay Alert - {station_name}"
        
        body = f"""
Train Delay Notification

Station: {station_name}
Service: {service_details}
Delay: {delay_minutes} minutes

This is an automated notification from the Train Platform Crawler service.
        """.strip()
        
        message = NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.EMAIL,
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
        Send a service disruption notification email.
        
        Args:
            recipient: Email address to send to
            station_name: Name of the station
            disruption_details: Details of the service disruption
            
        Returns:
            NotificationResult
        """
        subject = f"Service Disruption Alert - {station_name}"
        
        body = f"""
Service Disruption Notification

Station: {station_name}
Disruption: {disruption_details}

This is an automated notification from the Train Platform Crawler service.
        """.strip()
        
        message = NotificationMessage(
            recipient=recipient,
            subject=subject,
            body=body,
            notification_type=NotificationType.EMAIL,
            metadata={
                "station_name": station_name,
                "notification_type": "service_disruption"
            }
        )
        
        return self.send_if_enabled(message)
