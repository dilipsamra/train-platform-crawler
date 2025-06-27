"""Tests for notification system."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.notifications.base import (
    NotificationType, 
    NotificationPriority, 
    NotificationMessage, 
    NotificationResult,
    BaseNotifier,
    MockNotifier
)
from services.notifications.email_notifier import EmailNotifier
from services.notifications.sms_notifier import SMSNotifier
from services.notifications.push_notifier import PushNotifier
from services.notifications.notification_service import NotificationService
from core.exceptions import EmailNotificationError, SMSNotificationError, PushNotificationError


class TestNotificationMessage:
    """Test the NotificationMessage data class."""
    
    def test_notification_message_creation(self):
        """Test creating a notification message."""
        message = NotificationMessage(
            recipient="test@example.com",
            subject="Test Subject",
            body="Test Body",
            notification_type=NotificationType.EMAIL
        )
        
        assert message.recipient == "test@example.com"
        assert message.subject == "Test Subject"
        assert message.body == "Test Body"
        assert message.notification_type == NotificationType.EMAIL
        assert message.priority == NotificationPriority.NORMAL
        assert message.metadata == {}
    
    def test_notification_message_with_metadata(self):
        """Test creating a notification message with metadata."""
        metadata = {"station": "London", "delay": 10}
        message = NotificationMessage(
            recipient="test@example.com",
            subject="Test Subject",
            body="Test Body",
            notification_type=NotificationType.EMAIL,
            priority=NotificationPriority.HIGH,
            metadata=metadata
        )
        
        assert message.metadata == metadata
        assert message.priority == NotificationPriority.HIGH


class TestNotificationResult:
    """Test the NotificationResult data class."""
    
    def test_successful_result(self):
        """Test creating a successful notification result."""
        result = NotificationResult(
            success=True,
            message_id="msg_123",
            provider_response={"status": "sent"}
        )
        
        assert result.success is True
        assert result.message_id == "msg_123"
        assert result.error is None
        assert result.provider_response == {"status": "sent"}
    
    def test_failed_result(self):
        """Test creating a failed notification result."""
        result = NotificationResult(
            success=False,
            error="Failed to send"
        )
        
        assert result.success is False
        assert result.message_id is None
        assert result.error == "Failed to send"
        assert result.provider_response is None


class TestMockNotifier:
    """Test the MockNotifier implementation."""
    
    def test_mock_notifier_success(self):
        """Test mock notifier successful sending."""
        notifier = MockNotifier(NotificationType.EMAIL)
        
        message = NotificationMessage(
            recipient="test@example.com",
            subject="Test",
            body="Test body",
            notification_type=NotificationType.EMAIL
        )
        
        result = notifier.send(message)
        
        assert result.success is True
        assert result.message_id == "mock_1"
        assert len(notifier.sent_messages) == 1
        assert notifier.sent_messages[0] == message
    
    def test_mock_notifier_failure(self):
        """Test mock notifier failure simulation."""
        notifier = MockNotifier(NotificationType.EMAIL, should_fail=True)
        
        message = NotificationMessage(
            recipient="test@example.com",
            subject="Test",
            body="Test body",
            notification_type=NotificationType.EMAIL
        )
        
        result = notifier.send(message)
        
        assert result.success is False
        assert result.error == "Mock failure"
        assert len(notifier.sent_messages) == 0
    
    def test_mock_notifier_validation(self):
        """Test mock notifier recipient validation."""
        notifier = MockNotifier(NotificationType.EMAIL)
        
        assert notifier.validate_recipient("test@example.com") is True
        assert notifier.validate_recipient("") is False
        assert notifier.validate_recipient("   ") is False


class TestEmailNotifier:
    """Test the EmailNotifier implementation."""
    
    def test_email_validation(self):
        """Test email address validation."""
        with patch('core.config.get_settings') as mock_settings:
            mock_settings.return_value.smtp_host = "smtp.test.com"
            mock_settings.return_value.smtp_username = "test@test.com"
            mock_settings.return_value.smtp_password = "password"
            
            notifier = EmailNotifier()
            
            # Valid emails
            assert notifier.validate_recipient("test@example.com") is True
            assert notifier.validate_recipient("user.name+tag@domain.co.uk") is True
            
            # Invalid emails
            assert notifier.validate_recipient("invalid-email") is False
            assert notifier.validate_recipient("@domain.com") is False
            assert notifier.validate_recipient("user@") is False
            assert notifier.validate_recipient("") is False
    
    def test_email_notifier_disabled_without_config(self):
        """Test that email notifier is disabled without proper configuration."""
        with patch('core.config.get_settings') as mock_settings:
            mock_settings.return_value.smtp_host = None
            mock_settings.return_value.smtp_username = None
            mock_settings.return_value.smtp_password = None
            
            notifier = EmailNotifier()
            
            assert notifier.is_enabled() is False
    
    @patch('core.config.get_settings')
    @patch('smtplib.SMTP')
    def test_email_sending_success(self, mock_smtp, mock_settings):
        mock_settings.return_value.smtp_host = "smtp.test.com"
        mock_settings.return_value.smtp_port = 587
        mock_settings.return_value.smtp_username = "test@test.com"
        mock_settings.return_value.smtp_password = "password"
        mock_settings.return_value.smtp_use_tls = True
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        notifier = EmailNotifier(settings=mock_settings.return_value)
        
        message = NotificationMessage(
            recipient="recipient@example.com",
            subject="Test Subject",
            body="Test Body",
            notification_type=NotificationType.EMAIL
        )
        
        result = notifier.send(message)
        
        assert result.success is True
        assert result.message_id is not None
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@test.com", "password")
        assert mock_server.sendmail.called


class TestSMSNotifier:
    """Test the SMSNotifier implementation."""
    
    def test_phone_validation(self):
        """Test phone number validation."""
        with patch('core.config.get_settings') as mock_settings:
            mock_settings.return_value.twilio_account_sid = "test_sid"
            mock_settings.return_value.twilio_auth_token = "test_token"
            mock_settings.return_value.twilio_from_number = "+1234567890"
            
            notifier = SMSNotifier()
            
            # Valid phone numbers
            assert notifier.validate_recipient("+1234567890") is True
            assert notifier.validate_recipient("+447700900123") is True
            
            # Invalid phone numbers
            assert notifier.validate_recipient("1234567890") is False  # No +
            assert notifier.validate_recipient("+123") is False  # Too short
            assert notifier.validate_recipient("invalid") is False
            assert notifier.validate_recipient("") is False
    
    def test_sms_notifier_disabled_without_config(self):
        """Test that SMS notifier is disabled without proper configuration."""
        with patch('core.config.get_settings') as mock_settings:
            mock_settings.return_value.twilio_account_sid = None
            mock_settings.return_value.twilio_auth_token = None
            mock_settings.return_value.twilio_from_number = None
            
            notifier = SMSNotifier()
            
            assert notifier.is_enabled() is False


class TestPushNotifier:
    """Test the PushNotifier implementation."""
    
    def test_fcm_token_validation(self):
        """Test FCM token validation."""
        with patch('core.config.get_settings') as mock_settings:
            mock_settings.return_value.firebase_credentials_path = "/path/to/firebase.json"
            
            with patch('os.path.exists', return_value=True):
                notifier = PushNotifier()
                
                # Valid FCM token (simplified)
                valid_token = "a" * 150  # FCM tokens are typically long
                assert notifier.validate_recipient(valid_token) is True
                
                # Invalid tokens
                assert notifier.validate_recipient("short") is False
                assert notifier.validate_recipient("") is False
                assert notifier.validate_recipient("invalid@token") is False
    
    def test_push_notifier_disabled_without_config(self):
        """Test that push notifier is disabled without proper configuration."""
        with patch('core.config.get_settings') as mock_settings:
            mock_settings.return_value.firebase_credentials_path = None
            
            notifier = PushNotifier()
            
            assert notifier.is_enabled() is False


class TestNotificationService:
    """Test the NotificationService implementation."""
    
    def test_notification_service_with_mock_notifiers(self):
        """Test notification service with mock notifiers."""
        service = NotificationService(use_mock_notifiers=True)
        
        # Check that all notifiers are set up
        assert NotificationType.EMAIL in service.notifiers
        assert NotificationType.SMS in service.notifiers
        assert NotificationType.PUSH in service.notifiers
        
        # Check that they are mock notifiers
        assert isinstance(service.notifiers[NotificationType.EMAIL], MockNotifier)
        assert isinstance(service.notifiers[NotificationType.SMS], MockNotifier)
        assert isinstance(service.notifiers[NotificationType.PUSH], MockNotifier)
    
    def test_send_notification_success(self):
        """Test successful notification sending."""
        service = NotificationService(use_mock_notifiers=True)
        
        message = NotificationMessage(
            recipient="test@example.com",
            subject="Test",
            body="Test body",
            notification_type=NotificationType.EMAIL
        )
        
        result = service.send_notification(NotificationType.EMAIL, message)
        
        assert result.success is True
        assert result.message_id == "mock_1"
    
    def test_send_notification_invalid_type(self):
        """Test sending notification with invalid type."""
        service = NotificationService(use_mock_notifiers=True)
        
        # Remove a notifier to simulate missing type
        del service.notifiers[NotificationType.EMAIL]
        
        message = NotificationMessage(
            recipient="test@example.com",
            subject="Test",
            body="Test body",
            notification_type=NotificationType.EMAIL
        )
        
        result = service.send_notification(NotificationType.EMAIL, message)
        
        assert result.success is False
        assert "No notifier available" in result.error
    
    def test_multi_channel_notification(self):
        """Test sending notifications across multiple channels."""
        service = NotificationService(use_mock_notifiers=True)
        
        message = NotificationMessage(
            recipient="",  # Will be overridden
            subject="Test",
            body="Test body",
            notification_type=NotificationType.EMAIL  # Will be overridden
        )
        
        channels = [NotificationType.EMAIL, NotificationType.SMS]
        recipients = {
            NotificationType.EMAIL: "test@example.com",
            NotificationType.SMS: "+1234567890"
        }
        
        results = service.send_multi_channel_notification(message, channels, recipients)
        
        assert len(results) == 2
        assert results[NotificationType.EMAIL].success is True
        assert results[NotificationType.SMS].success is True
    
    def test_train_delay_alert(self):
        """Test sending train delay alerts."""
        service = NotificationService(use_mock_notifiers=True)
        
        recipients = {
            NotificationType.EMAIL: "test@example.com",
            NotificationType.SMS: "+1234567890"
        }
        
        results = service.send_train_delay_alert(
            station_name="London Paddington",
            service_details="09:15 to Reading",
            delay_minutes=10,
            recipients=recipients
        )
        
        assert len(results) == 2
        assert results[NotificationType.EMAIL].success is True
        assert results[NotificationType.SMS].success is True
    
    def test_service_disruption_alert(self):
        """Test sending service disruption alerts."""
        service = NotificationService(use_mock_notifiers=True)
        
        recipients = {
            NotificationType.EMAIL: "test@example.com"
        }
        
        results = service.send_service_disruption_alert(
            station_name="London Paddington",
            disruption_details="Signal failure causing delays",
            recipients=recipients
        )
        
        assert len(results) == 1
        assert results[NotificationType.EMAIL].success is True
    
    def test_notifier_status(self):
        """Test getting notifier status."""
        service = NotificationService(use_mock_notifiers=True)
        
        status = service.get_notifier_status()
        
        assert "email" in status
        assert "sms" in status
        assert "push" in status
        
        assert status["email"]["enabled"] is True
        assert status["email"]["type"] == "MockNotifier"
    
    def test_enable_disable_notifier(self):
        """Test enabling and disabling notifiers."""
        service = NotificationService(use_mock_notifiers=True)
        
        # Disable email notifier
        service.disable_notifier(NotificationType.EMAIL)
        assert service.notifiers[NotificationType.EMAIL].is_enabled() is False
        
        # Enable email notifier
        service.enable_notifier(NotificationType.EMAIL)
        assert service.notifiers[NotificationType.EMAIL].is_enabled() is True
