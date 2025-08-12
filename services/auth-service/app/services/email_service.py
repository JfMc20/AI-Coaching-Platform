"""
Email Service
Handles sending emails for password reset and other authentication flows
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending authentication-related emails"""
    
    def __init__(self):
        # Email configuration
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        self.email_service_enabled = os.getenv("EMAIL_SERVICE_ENABLED", "false").lower() == "true"
        self.from_email = os.getenv("FROM_EMAIL", "noreply@example.com")
        self.from_name = os.getenv("FROM_NAME", "MVP Coaching AI Platform")
        
        # SMTP configuration (for future implementation)
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    
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
            
            # Log email details (in a real implementation, this would be sent via email service)
            logger.info("Password reset email prepared", extra={
                "email": email,
                "reset_url": reset_url,
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
                logger.info(f"Body: Click the following link to reset your password: {reset_url}")
                logger.info(f"Reset token (first 16 chars): {reset_token[:16]}...")
                return True
                
        except Exception as e:
            logger.error("Failed to send password reset email", extra={
                "email": email,
                "error": str(e),
                "client_ip": client_ip
            })
            return False


# Dependency provider for FastAPI
def get_email_service() -> EmailService:
    """Get email service instance"""
    return EmailService()