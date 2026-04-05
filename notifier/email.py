"""
Email notifier for sending Excel files via Gmail SMTP.
"""
import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from typing import Optional

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Send Excel files via Gmail SMTP."""
    
    def __init__(self, email: str, app_password: str, to_emails: str):
        """
        Initialize email notifier.
        
        Args:
            email: Gmail address (your email)
            app_password: Gmail App Password (16 chars, no spaces)
            to_emails: Destination email(s), comma separated
        """
        self.email = email
        self.app_password = app_password.replace(" ", "")  # Remove spaces
        self.to_emails = [e.strip() for e in to_emails.split(",")]
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
    
    def send_excel(self, filepath: str, subject: str = None, body: str = None) -> bool:
        """
        Send Excel file via email.
        
        Args:
            filepath: Path to the Excel file
            subject: Email subject (optional)
            body: Email body (optional)
        
        Returns:
            True if sent successfully
        """
        if not filepath or not os.path.exists(filepath):
            logger.error(f"Archivo no encontrado: {filepath}")
            return False
        
        # Default subject and body
        if subject is None:
            from datetime import datetime
            today = datetime.now().strftime("%Y-%m-%d")
            subject = f"Libros Buscalibre - {today}"
        
        if body is None:
            body = "Adjunto el Excel con los libros scrapeados de hoy."
        
        return self._send_email(subject, body, filepath)
    
    def _send_email(self, subject: str, body: str, attachment_path: str) -> bool:
        """Send email with attachment."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = ", ".join(self.to_emails)
            msg["Subject"] = subject
            
            # Attach body
            msg.attach(MIMEText(body, "plain"))
            
            # Attach Excel file
            with open(attachment_path, "rb") as f:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            filename = os.path.basename(attachment_path)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {filename}"
            )
            msg.attach(part)
            
            # Connect to Gmail SMTP
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.app_password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email enviado a {self.to_emails}")
            return True
            
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            return False