import pytz
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Host(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hostname = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(20), default='offline')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(pytz.UTC))
    status_events = db.relationship('HostStatusEvent', backref='host', lazy=True)
    status_switches = db.relationship('StatusSwitch', backref='host', lazy=True)

    def get_status_statistics(self):
        utc = pytz.UTC
        cet = pytz.timezone('Europe/Warsaw')  # Using Europe/Warsaw instead of CET for proper DST handling
        current_time_utc = datetime.now(utc)

        # Ensure created_at is timezone-aware
        created_at_utc = self.created_at if self.created_at.tzinfo else utc.localize(self.created_at)

        # Fetch all status events and ensure their timestamps are timezone-aware
        status_events = HostStatusEvent.query.filter_by(host_id=self.id).order_by(HostStatusEvent.timestamp).all()
        
        # Helper function to ensure timezone awareness
        def ensure_tz_aware(dt):
            return dt if dt.tzinfo else utc.localize(dt)

        total_uptime = 0
        total_downtime = 0
        last_online = None
        last_offline = None

        if not status_events:
            # If there are no events but we have a current status, count from created_at
            if self.status in ['online', 'offline']:
                interval = (current_time_utc - created_at_utc).total_seconds()
                if self.status == 'online':
                    total_uptime = interval
                    last_online = created_at_utc
                else:
                    total_downtime = interval
                    last_offline = created_at_utc
        else:
            # Calculate from first event to handle initial period
            first_event = status_events[0]
            first_event_time = ensure_tz_aware(first_event.timestamp)
            initial_interval = (first_event_time - created_at_utc).total_seconds()
            if first_event.status == 'online':
                total_downtime += initial_interval  # Was offline before first online
                last_offline = created_at_utc
            else:
                total_uptime += initial_interval  # Was online before first offline
                last_online = created_at_utc

            # Calculate intervals between events
            for event in status_events:
                interval = event.interval or 0  # Use 0 if interval is None
                event_time = ensure_tz_aware(event.timestamp)
                if event.status == 'online':
                    total_uptime += interval
                    last_online = event_time
                elif event.status == 'offline':
                    total_downtime += interval
                    last_offline = event_time

            # Handle the current ongoing interval
            last_event = status_events[-1]
            last_event_time = ensure_tz_aware(last_event.timestamp)
            ongoing_interval = (current_time_utc - last_event_time).total_seconds()
            if last_event.status == 'online':
                total_uptime += ongoing_interval
            elif last_event.status == 'offline':
                total_downtime += ongoing_interval

        # Format duration and timestamps
        def format_duration(seconds):
            if seconds is None:
                return 'N/A'
            else:
                seconds = int(seconds)
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                secs = seconds % 60
                return f"{hours}h {minutes}m {secs}s"

        def format_timestamp(ts):
            if ts is None:
                return 'N/A'
            else:
                ts_cet = ts.astimezone(cet)
                return ts_cet.strftime('%#d.%#m.%Y, %H:%M:%S')  # Using %#d and %#m for Windows

        # Calculate uptime ratio
        total_time = total_uptime + total_downtime
        uptime_ratio = (total_uptime / total_time * 100) if total_time > 0 else 0

        return {
            'status': self.status,
            'total_uptime': format_duration(total_uptime),
            'total_downtime': format_duration(total_downtime),
            'last_online': format_timestamp(last_online),
            'last_offline': format_timestamp(last_offline),
            'uptime_ratio': round(uptime_ratio, 1)
        }

    def update_status(self, new_status):
        """Update host status and create a new status event.
        Returns True if status changed, False otherwise."""
        if self.status == new_status:
            return False

        utc = pytz.UTC
        current_time = datetime.now(utc)
        
        # Get the last event to update its interval
        last_event = HostStatusEvent.query.filter_by(host_id=self.id).order_by(HostStatusEvent.timestamp.desc()).first()
        
        # Create new event
        new_event = HostStatusEvent(
            host_id=self.id,
            status=new_status,
            timestamp=current_time
        )
        
        # Update interval of last event if it exists
        if last_event:
            last_event_time = last_event.timestamp if last_event.timestamp.tzinfo else utc.localize(last_event.timestamp)
            last_event.interval = (new_event.timestamp - last_event_time).total_seconds()
        
        # Create status switch event only if there's no recent switch of the same type
        switch_type = 'bootup' if new_status == 'online' else 'shutdown'
        
        # Check for recent switch events (within last 5 seconds)
        recent_switch = StatusSwitch.query.filter(
            StatusSwitch.host_id == self.id,
            StatusSwitch.switch_type == switch_type,
            StatusSwitch.timestamp >= current_time - timedelta(seconds=5)
        ).first()
        
        if not recent_switch:
            status_switch = StatusSwitch(
                host_id=self.id,
                switch_type=switch_type,
                timestamp=current_time
            )
            db.session.add(status_switch)
        
        # Update host status
        self.status = new_status
        
        # Save changes
        db.session.add(new_event)
        db.session.commit()
        
        return True

class HostStatusEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('host.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(pytz.UTC))
    interval = db.Column(db.Float, nullable=False, default=0)  # Time in seconds since last event

class StatusSwitch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('host.id'), nullable=False)
    switch_type = db.Column(db.String(20), nullable=False)  # 'bootup' or 'shutdown'
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(pytz.UTC))
    is_read = db.Column(db.Boolean, default=False)
    notification_text = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'host_id': self.host_id,
            'switch_type': self.switch_type,
            'timestamp': self.timestamp.isoformat(),
            'is_read': self.is_read,
            'notification_text': self.notification_text,
            'host_name': self.host.hostname if self.host else None,
            'host_ip': self.host.ip_address if self.host else None
        }