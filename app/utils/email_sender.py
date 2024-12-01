from flask_mail import Mail, Message
from flask import current_app
import logging

logger = logging.getLogger(__name__)
mail = Mail()

class EmailSender:
    @staticmethod
    def send_status_notification(host, status):
        if not host.notification_emails or not host.email_notifications_enabled:
            return

        recipients = [email.strip() for email in host.notification_emails.split(',')]
        if not recipients:
            return

        subject = f"Host {host.hostname} is {status}"
        template = get_email_template(status, host)

        try:
            msg = Message(
                subject=subject,
                recipients=recipients,
                html=template,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            mail.send(msg)
            logger.info(f"Status notification email sent for host {host.hostname} ({status})")
        except Exception as e:
            logger.error(f"Failed to send status notification email for host {host.hostname}: {str(e)}")

def get_email_template(status, host):
    if status == 'online':
        return f"""
        <h2>Host Status Update: Online</h2>
        <p>Your host <strong>{host.hostname}</strong> is now online.</p>
        <ul>
            <li>Host: {host.hostname}</li>
            <li>IP Address: {host.ip_address}</li>
            <li>Status: Online</li>
            <li>Time: {host.status_events[-1].timestamp if host.status_events else 'N/A'}</li>
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
            <li>Time: {host.status_events[-1].timestamp if host.status_events else 'N/A'}</li>
        </ul>
        """
