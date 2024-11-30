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
    hostname = db.Column(db.String(80))
    ip_address = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='unknown')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.UTC))
    status_events = db.relationship('HostStatusEvent', backref='host', lazy=True)
    status_switches = db.relationship('StatusSwitch', backref='host', lazy=True)

    def get_status_statistics(self):
        utc = pytz.UTC
        cet = pytz.timezone('CET')
        current_time_utc = datetime.now(utc)

        # Fetch all status events
        status_events = HostStatusEvent.query.filter_by(host_id=self.id).order_by(HostStatusEvent.timestamp).all()

        total_uptime = 0
        total_downtime = 0
        last_online = None
        last_offline = None

        if not status_events:
            # If there are no events but we have a current status, count from created_at
            if self.status in ['online', 'offline']:
                interval = (current_time_utc - self.created_at).total_seconds()
                if self.status == 'online':
                    total_uptime = interval
                    last_online = self.created_at
                else:
                    total_downtime = interval
                    last_offline = self.created_at
        else:
            # Calculate from first event to handle initial period
            first_event = status_events[0]
            initial_interval = (first_event.timestamp - self.created_at).total_seconds()
            if first_event.status == 'online':
                total_downtime += initial_interval  # Was offline before first online
                last_offline = self.created_at
            else:
                total_uptime += initial_interval  # Was online before first offline
                last_online = self.created_at

            # Calculate intervals between events
            for event in status_events:
                interval = event.interval
                if event.status == 'online':
                    total_uptime += interval
                    last_online = event.timestamp
                elif event.status == 'offline':
                    total_downtime += interval
                    last_offline = event.timestamp

            # Handle the current ongoing interval
            last_event = status_events[-1]
            ongoing_interval = (current_time_utc - last_event.timestamp).total_seconds()
            if last_event.status == 'online':
                total_uptime += ongoing_interval
            elif last_event.status == 'offline':
                total_downtime += ongoing_interval

        # Fetch last bootup and shutdown events
        last_bootup = StatusSwitch.query.filter_by(host_id=self.id, switch_type='bootup').order_by(StatusSwitch.timestamp.desc()).first()
        last_shutdown = StatusSwitch.query.filter_by(host_id=self.id, switch_type='shutdown').order_by(StatusSwitch.timestamp.desc()).first()

        # Calculate last uptime
        if last_bootup:
            next_shutdown = StatusSwitch.query.filter(
                StatusSwitch.host_id == self.id,
                StatusSwitch.switch_type == 'shutdown',
                StatusSwitch.timestamp > last_bootup.timestamp
            ).order_by(StatusSwitch.timestamp).first()

            if next_shutdown:
                last_uptime = (next_shutdown.timestamp - last_bootup.timestamp).total_seconds()
            else:
                last_uptime = (current_time_utc - last_bootup.timestamp).total_seconds()
        else:
            last_uptime = None

        # Calculate last downtime
        if last_shutdown:
            next_bootup = StatusSwitch.query.filter(
                StatusSwitch.host_id == self.id,
                StatusSwitch.switch_type == 'bootup',
                StatusSwitch.timestamp > last_shutdown.timestamp
            ).order_by(StatusSwitch.timestamp).first()

            if next_bootup:
                last_downtime = (next_bootup.timestamp - last_shutdown.timestamp).total_seconds()
            else:
                last_downtime = (current_time_utc - last_shutdown.timestamp).total_seconds()
        else:
            last_downtime = None

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
                return ts_cet.strftime('%Y-%m-%d %H:%M:%S')

        # Calculate uptime ratio
        total_time = total_uptime + total_downtime
        uptime_ratio = (total_uptime / total_time * 100) if total_time > 0 else 0

        return {
            'status': self.status,
            'total_uptime': format_duration(total_uptime),
            'total_downtime': format_duration(total_downtime),
            'last_online': format_timestamp(last_online),
            'last_offline': format_timestamp(last_offline),
            'last_uptime': format_duration(last_uptime),
            'last_downtime': format_duration(last_downtime),
            'uptime_ratio': round(uptime_ratio, 1)
        }

    def update_status(self, new_status):
        """Update host status and create a new status event.
        Returns True if status changed, False otherwise."""
        if self.status == new_status:
            return False

        # Get the last event to update its interval
        last_event = HostStatusEvent.query.filter_by(host_id=self.id).order_by(HostStatusEvent.timestamp.desc()).first()
        
        # Create new event
        new_event = HostStatusEvent(
            host_id=self.id,
            status=new_status,
            timestamp=datetime.now(pytz.UTC)
        )
        
        # Update interval of last event if it exists
        if last_event:
            last_event.interval = (new_event.timestamp - last_event.timestamp).total_seconds()
        
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
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.UTC))
    interval = db.Column(db.Float, default=0)  # Duration in seconds

class StatusSwitch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('host.id'), nullable=False)
    switch_type = db.Column(db.String(20), nullable=False)  # 'bootup' or 'shutdown'
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.UTC))