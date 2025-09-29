import logging
import os
from typing import Optional

import resend

from app.models.config import EmailConfig

logger = logging.getLogger(__name__)

_email_initialized = False


def validate_email_config(config: EmailConfig) -> None:
    """Validate email configuration"""
    if not config.sender or not config.sender.strip():
        raise ValueError("Email sender is required")

    if not config.receiver or not config.receiver.strip():
        raise ValueError("Email receiver is required")

    if not config.api_key or not config.api_key.strip():
        raise ValueError("Email API key is required")

    # Basic email format validation
    if "@" not in config.sender:
        raise ValueError("Invalid sender email format")

    if "@" not in config.receiver:
        raise ValueError("Invalid receiver email format")


def init_email(config: EmailConfig, force_reinit: bool = False) -> None:
    """Initialize email service with validation"""
    global _email_initialized

    if _email_initialized and not force_reinit:
        logger.warning("Email service already initialized")
        return

    try:
        # Validate configuration
        validate_email_config(config)

        # Initialize Resend
        resend.api_key = config.api_key


        _email_initialized = True
        logger.info(f"Email service initialized successfully. Sender: {config.sender}")

    except Exception as e:
        logger.error(f"Failed to initialize email service: {e}")
        _email_initialized = False
        raise


def is_email_initialized() -> bool:
    """Check if email service is initialized"""
    return _email_initialized


def get_email_config_from_env() -> Optional[EmailConfig]:
    """Get email configuration from environment variables"""
    sender = os.getenv("EMAIL_SENDER")
    receiver = os.getenv("EMAIL_RECEIVER")
    api_key = os.getenv("EMAIL_API_KEY")

    if not all([sender, receiver, api_key]):
        return None

    return EmailConfig(sender=sender, receiver=receiver, api_key=api_key)


def reset_email_service() -> None:
    """Reset email service state (useful for testing)"""
    global _email_initialized
    _email_initialized = False
