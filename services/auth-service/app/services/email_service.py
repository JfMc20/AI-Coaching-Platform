"""
Email Service
Handles sending emails for password reset and other authentication flows

This service has been migrated to use the centralized environment constants system
located in shared.config.env_constants for consistent configuration management.
"""

import hashlib
import logging
from typing import Optional

from shared.config.env_constants import (
    FRONTEND_URL,
    EMAIL_SERVICE_ENABLED,
    FROM_EMAIL,
    FROM_NAME,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_USER,
    SMTP_PASSWORD,
    SMTP_USE_TLS,
    get_env_value
)

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending authentication-related emails"""
    
    def _parse_smtp_port(self, port_str: str) -> int:
        """
        Safely parse SMTP port from environment variable
        
        Args:
            port_str: Port value from environment variable
            
        Returns:
            Valid port number (1-65535) or default 587
        """
        try:
            port = int(port_str)
            if 1 <= port <= 65535:
                return port
            else:
                logger.warning(f"SMTP port {port} is out of valid range (1-65535), using default 587")
                return 587
        except (ValueError, TypeError):
            logger.warning(f"Invalid SMTP port value '{port_str}', using default 587")
            return 587
    
    def _generate_token_hash(self, token: str) -> str:
        """
        Generate a safe hash of the token for logging purposes
        
        Args:
            token: The reset token
            
        Returns:
            SHA-256 hex digest of the token
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()
    
    def __init__(self):
        # Email configuration - using centralized environment constants
        self.frontend_url = get_env_value(FRONTEND_URL, fallback=True) or "http://localhost:3000"
        self.email_service_enabled = (get_env_value(EMAIL_SERVICE_ENABLED, fallback=True) or "false").lower() == "true"
        self.from_email = get_env_value(FROM_EMAIL, fallback=True) or "noreply@example.com"
        self.from_name = get_env_value(FROM_NAME, fallback=True) or "MVP Coaching AI Platform"
        
        # SMTP configuration (for future implementation) - using centralized environment constants
        self.smtp_host = get_env_value(SMTP_HOST, fallback=True) or ""
        self.smtp_port = self._parse_smtp_port(get_env_value(SMTP_PORT, fallback=True) or "587")
        self.smtp_user = get_env_value(SMTP_USER, fallback=True) or ""
        self.smtp_password = get_env_value(SMTP_PASSWORD, fallback=True) or ""
        self.smtp_use_tls = (get_env_value(SMTP_USE_TLS, fallback=True) or "true").lower() == "true"
    
    def send_password_reset_email(self, email: str, reset_token: str, client_ip: Optional[str] = None) -> bool:
        """
        Send password reset email to creator
        
        Args:
            email: Creator's email address
            reset_token: Password reset token
            client_ip: Client IP address (for logging)
            
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Construct reset URL
            reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"
            
            # Generate safe token hash for logging
            token_hash = self._generate_token_hash(reset_token)
            
            # Log email details (in a real implementation, this would be sent via email service)
            logger.info("Password reset email prepared", extra={
                "email": email,
                "token_hash": token_hash,  # Safe hash instead of raw token
                "client_ip": client_ip
            })
            
            # In a real implementation, you would integrate with an email service like SendGrid
            # For now, we're just logging the details
            if self.email_service_enabled:
                # This is where you would implement actual email sending
                # Example with SendGrid:
                # sg = sendgrid.SendGridAPIClient(api_key=os.getenv("SENDGRID_API_KEY"))
                # from_email = Email(self.from_email, self.from_name)
                # to_email = To(email)
                # subject = "Password Reset Request"
                # content = Content(
                #     "text/html",
                #     f"<p>Click <a href='{reset_url}'>here</a> to reset your password.</p>"
                # )
                # mail = Mail(from_email, to_email, subject, content)
                # response = sg.client.mail.send.post(request_body=mail.get())
                # return response.status_code == 202
                logger.warning("Email service is enabled but not implemented")
                return False
            else:
                # Email service is disabled, just log the details
                logger.info("Email service is disabled. Would send email with the following details:")
                logger.info(f"To: {email}")
                logger.info(f"Subject: Password Reset Request")
                logger.info(f"Body: Click the following link to reset your password: [RESET_URL_REDACTED]")
                logger.info(f"Reset token hash (SHA-256): {token_hash}")
                return True
                
        except Exception as e:
            # Generate safe token hash for error logging
            token_hash = self._generate_token_hash(reset_token)
            logger.error("Failed to send password reset email", extra={
                "email": email,
                "token_hash": token_hash,  # Safe hash for traceability
                "error": str(e),
                "client_ip": client_ip
            })
            return False


# Dependency provider for FastAPI
def get_email_service() -> EmailService:
    """Get email service instance"""
    return EmailService()