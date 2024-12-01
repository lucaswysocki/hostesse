from flask_mail import Message
from flask import current_app
import logging
from app import mail
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailSender:
    @staticmethod
    def send_status_notification(host, status):
        if not host.notification_emails or not host.email_notifications_enabled:
            logger.info(f"Email notifications not enabled for host {host.hostname}")
            return

        recipients = [email.strip() for email in host.notification_emails.split(',')]
        if not recipients:
            logger.warning(f"No valid recipients found for host {host.hostname}")
            return

        subject = f"Host {host.hostname} is {status}"
        template = get_email_template(status, host)

        try:
            logger.debug(f"Attempting to send email notification to {recipients}")
            logger.debug(f"Using sender: {current_app.config['MAIL_DEFAULT_SENDER']}")
            msg = Message(
                subject=subject,
                recipients=recipients,
                html=template,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            logger.debug("Message object created successfully")
            
            # Test SMTP connection before sending
            with mail.connect() as conn:
                logger.debug("SMTP connection established")
                conn.send(msg)
            
            logger.info(f"Status notification email sent for host {host.hostname} ({status}) to {recipients}")
        except Exception as e:
            logger.error(f"Failed to send status notification email for host {host.hostname}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {str(e)}")
            if hasattr(e, 'smtp_error'):
                logger.error(f"SMTP error: {e.smtp_error}")
            if hasattr(e, 'smtp_code'):
                logger.error(f"SMTP code: {e.smtp_code}")

def get_email_template(status, host):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if status == 'online':
        return f"""
        <h2>Host Status Update: Online</h2>
        <p>Your host <strong>{host.hostname}</strong> is now online.</p>
        <ul>
            <li>Host: {host.hostname}</li>
            <li>IP Address: {host.ip_address}</li>
            <li>Status: Online</li>
            <li>Time: {current_time}</li>
        </ul>
        """
    else:
        return f"""
        <h2>Host Status Update: Offline</h2>
        <p>Your host <strong>{host.hostname}</strong> is now offline.</p>
        <ul>
            <li>Host: {host.hostname}</li>
            <li>IP Address: {host.ip_address}</li>
            <li>Status: Offline</li>
            <li>Time: {current_time}</li>
        </ul>
        """
