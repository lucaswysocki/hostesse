import os
from dotenv import load_dotenv
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

class Config:
    # Existing configurations...
    
    # Email Configuration with validation
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    if not MAIL_SERVER:
        logger.warning("MAIL_SERVER not set in environment, using default: smtp.gmail.com")
        MAIL_SERVER = 'smtp.gmail.com'

    try:
        MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    except (TypeError, ValueError):
        logger.warning("Invalid MAIL_PORT in environment, using default: 587")
        MAIL_PORT = 587

    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    if not MAIL_USERNAME:
        logger.error("MAIL_USERNAME not set in environment variables!")
        
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    if not MAIL_PASSWORD:
        logger.error("MAIL_PASSWORD not set in environment variables!")
        
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    if not MAIL_DEFAULT_SENDER:
        logger.warning("MAIL_DEFAULT_SENDER not set, using MAIL_USERNAME as default sender")
        MAIL_DEFAULT_SENDER = MAIL_USERNAME

    # Log all email configuration values
    def __init__(self):
        logger.info("Email Configuration:")
        logger.info(f"MAIL_SERVER: {self.MAIL_SERVER}")
        logger.info(f"MAIL_PORT: {self.MAIL_PORT}")
        logger.info(f"MAIL_USE_TLS: {self.MAIL_USE_TLS}")
        logger.info(f"MAIL_USERNAME: {'Set' if self.MAIL_USERNAME else 'Not Set'}")
        logger.info(f"MAIL_PASSWORD: {'Set' if self.MAIL_PASSWORD else 'Not Set'}")
        logger.info(f"MAIL_DEFAULT_SENDER: {self.MAIL_DEFAULT_SENDER}")
