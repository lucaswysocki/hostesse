from datetime import datetime
from ping3 import ping
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
import logging
from app import db
from app.models import Host, HostStatusEvent
from sqlalchemy import func
import pytz
from app.utils.email_sender import EmailSender

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HostChecker:
    def __init__(self, app):
        self.app = app

    def cleanup_old_events(self, host_id, max_events=1000):
        """Delete oldest events when count exceeds max_events"""
        try:
            utc = pytz.UTC
            count = HostStatusEvent.query.filter_by(host_id=host_id).count()
            if count > max_events:
                # Find the timestamp of the max_events-th most recent event
                cutoff_event = HostStatusEvent.query.filter_by(host_id=host_id)\
                    .order_by(HostStatusEvent.timestamp.desc())\
                    .offset(max_events).first()
                
                if cutoff_event:
                    cutoff_time = cutoff_event.timestamp if cutoff_event.timestamp.tzinfo else utc.localize(cutoff_event.timestamp)
                    # Delete all events older than the cutoff
                    HostStatusEvent.query.filter_by(host_id=host_id)\
                        .filter(HostStatusEvent.timestamp < cutoff_time)\
                        .delete()
                    db.session.commit()
                    logger.info(f"Cleaned up old events for host {host_id}")
        except Exception as e:
            logger.error(f"Error cleaning up events for host {host_id}: {str(e)}")

    def check_host_status(self, host):
        try:
            response_time = ping(host.ip_address, timeout=2)
            new_status = 'online' if response_time is not None else 'offline'
            
            # Check if status has changed and update the database
            if new_status != host.status:
                logger.info(f"Host {host.hostname} status changed from {host.status} to {new_status}")
                
                # Update host status in database first
                host.status = new_status
                db.session.commit()
                
                # Create status event
                event = HostStatusEvent(host_id=host.id, status=new_status)
                db.session.add(event)
                db.session.commit()
                
                # Send email notification if enabled
                if host.email_notifications_enabled:
                    EmailSender.send_status_notification(host, new_status)
                
                # Cleanup old events
                self.cleanup_old_events(host.id)
            
            logger.info(f"Host {host.ip_address} status recorded as {new_status}")
            return new_status
            
        except Exception as e:
            logger.error(f"Error checking host {host.hostname} status: {str(e)}")
            return 'unknown'

    def check_all_hosts(self):
        with self.app.app_context():
            try:
                hosts = Host.query.all()
                for host in hosts:
                    self.check_host_status(host)
            except Exception as e:
                logger.error(f"Error in check_all_hosts: {str(e)}")

_scheduler = None

def init_scheduler(app):
    global _scheduler
    
    # If scheduler already exists and is running, return it
    if _scheduler is not None and _scheduler.running:
        logger.info("Using existing scheduler")
        return _scheduler
    
    # If there's an existing scheduler that's not running, shut it down
    if _scheduler is not None:
        logger.info("Shutting down existing scheduler")
        _scheduler.shutdown()
    
    # Create new scheduler with memory jobstore
    _scheduler = BackgroundScheduler(
        jobstores={'default': MemoryJobStore()},
        timezone=pytz.timezone('Europe/Warsaw')
    )
    
    host_checker = HostChecker(app)
    
    # Remove any existing jobs with the same ID
    _scheduler.remove_all_jobs()
    
    _scheduler.add_job(
        id='check_hosts',
        func=host_checker.check_all_hosts,
        trigger='interval',
        seconds=30,  # Check every 30 seconds
        replace_existing=True,
        max_instances=1,  # Ensure only one instance runs at a time
        coalesce=True    # Combine multiple executions of the same job into one
    )
    
    if not _scheduler.running:
        _scheduler.start()
        logger.info("Scheduler started successfully")
    
    return _scheduler
