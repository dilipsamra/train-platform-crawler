"""Tests for core configuration module."""

import pytest
import os
from unittest.mock import patch
from core.config import Settings, get_settings


class TestSettings:
    """Test the Settings class."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = Settings()
        
        assert settings.app_name == "Train Platform Crawler API"
        assert settings.app_version == "1.0.0"
        assert settings.environment == "development"
        assert settings.debug is True
        assert settings.log_level == "INFO"
        assert settings.cors_origins == ["*"]
        assert settings.cors_allow_credentials is True
        assert settings.cors_allow_methods == ["*"]
        assert settings.cors_allow_headers == ["*"]
    
    def test_environment_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'APP_NAME': 'Test App',
            'APP_VERSION': '2.0.0',
            'ENVIRONMENT': 'production',
            'DEBUG': 'false',
            'LOG_LEVEL': 'ERROR'
        }):
            settings = Settings()
            
            assert settings.app_name == "Test App"
            assert settings.app_version == "2.0.0"
            assert settings.environment == "production"
            assert settings.debug is False
            assert settings.log_level == "ERROR"
    
    def test_api_configuration(self):
        """Test API-related configuration."""
        with patch.dict(os.environ, {
            'CONSUMER_KEY': 'test_key',
            'CONSUMER_SECRET': 'test_secret',
            'LDBWS_BASE_URL': 'https://test.api.com'
        }):
            settings = Settings()
            
            assert settings.consumer_key == "test_key"
            assert settings.consumer_secret == "test_secret"
            assert settings.ldbws_base_url == "https://test.api.com"
    
    def test_notification_configuration(self):
        """Test notification-related configuration."""
        with patch.dict(os.environ, {
            'SMTP_HOST': 'smtp.test.com',
            'SMTP_PORT': '587',
            'SMTP_USERNAME': 'test@test.com',
            'SMTP_PASSWORD': 'password',
            'SMTP_USE_TLS': 'true',
            'TWILIO_ACCOUNT_SID': 'test_sid',
            'TWILIO_AUTH_TOKEN': 'test_token',
            'TWILIO_FROM_NUMBER': '+1234567890',
            'FIREBASE_CREDENTIALS_PATH': '/path/to/firebase.json'
        }):
            settings = Settings()
            
            assert settings.smtp_host == "smtp.test.com"
            assert settings.smtp_port == 587
            assert settings.smtp_username == "test@test.com"
            assert settings.smtp_password == "password"
            assert settings.smtp_use_tls is True
            assert settings.twilio_account_sid == "test_sid"
            assert settings.twilio_auth_token == "test_token"
            assert settings.twilio_from_number == "+1234567890"
            assert settings.firebase_credentials_path == "/path/to/firebase.json"
    
    def test_cors_configuration(self):
        """Test CORS configuration."""
        with patch.dict(os.environ, {
            'CORS_ORIGINS': '["http://localhost:3000", "https://example.com"]',
            'CORS_ALLOW_CREDENTIALS': 'false',
            'CORS_ALLOW_METHODS': '["GET", "POST"]',
            'CORS_ALLOW_HEADERS': '["Content-Type", "Authorization"]'
        }):
            settings = Settings()
            
            assert settings.cors_origins == ["http://localhost:3000", "https://example.com"]
            assert settings.cors_allow_credentials is False
            assert settings.cors_allow_methods == ["GET", "POST"]
            assert settings.cors_allow_headers == ["Content-Type", "Authorization"]


class TestGetSettings:
    """Test the get_settings function."""
    
    def test_singleton_behavior(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_settings_caching(self):
        """Test that settings are cached properly."""
        # Clear any existing cache
        get_settings.cache_clear()
        
        with patch.dict(os.environ, {'APP_NAME': 'Cached App'}):
            settings1 = get_settings()
            assert settings1.app_name == "Cached App"
        
        # Change environment variable but should still get cached value
        with patch.dict(os.environ, {'APP_NAME': 'New App'}):
            settings2 = get_settings()
            assert settings2.app_name == "Cached App"  # Should be cached value
            assert settings1 is settings2
        
        # Clear cache and get new settings
        get_settings.cache_clear()
        with patch.dict(os.environ, {'APP_NAME': 'New App'}):
            settings3 = get_settings()
            assert settings3.app_name == "New App"  # Should be new value
            assert settings1 is not settings3
