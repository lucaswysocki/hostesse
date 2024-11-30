from app import create_app, db
from app.models import Host, HostStatusEvent
from datetime import datetime
from sqlalchemy import and_

def cleanup_events():
    print("Starting event cleanup...")
    app = create_app()
    
    with app.app_context():
        # Get all hosts
        hosts = Host.query.all()
        total_removed = 0
        
        for host in hosts:
            print(f"\nProcessing host {host.id}...")
            
            # Get all events for this host ordered by timestamp
            events = HostStatusEvent.query.filter_by(host_id=host.id)\
                .order_by(HostStatusEvent.timestamp.asc())\
                .all()
            
            if not events:
                print(f"No events found for host {host.id}")
                continue
                
            print(f"Found {len(events)} events")
            
            # Keep track of events to preserve
            events_to_preserve = []
            last_status = None
            last_timestamp = None
            
            # Iterate through events chronologically
            for event in events:
                # Skip duplicate events (same status at exact same timestamp)
                if last_timestamp == event.timestamp and last_status == event.status:
                    continue
                    
                # Skip events with same status unless it's the first one
                if last_status == event.status:
                    continue
                    
                # Keep this event's data
                events_to_preserve.append({
                    'status': event.status,
                    'timestamp': event.timestamp
                })
                last_status = event.status
                last_timestamp = event.timestamp
            
            # Calculate how many events will be removed
            events_to_remove = len(events) - len(events_to_preserve)
            total_removed += events_to_remove
            
            print(f"Keeping {len(events_to_preserve)} events, removing {events_to_remove} duplicates")
            
            if events_to_remove > 0:
                # Delete all events for this host
                HostStatusEvent.query.filter_by(host_id=host.id).delete()
                
                # Create new events with preserved data
                for event_data in events_to_preserve:
                    new_event = HostStatusEvent(
                        host_id=host.id,
                        status=event_data['status'],
                        timestamp=event_data['timestamp']
                    )
                    db.session.add(new_event)
                
                # Make sure the host's current status matches the last event
                if events_to_preserve:
                    host.status = events_to_preserve[-1]['status']
                
                db.session.commit()
        
        print(f"\nCleanup complete! Removed {total_removed} duplicate events.")

if __name__ == '__main__':
    cleanup_events()
