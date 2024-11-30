from app import create_app, db
from app.models import Host, HostStatusEvent, StatusSwitch
from datetime import datetime

def migrate_to_switches():
    print("Starting migration to switches...")
    app = create_app()
    
    with app.app_context():
        # Create the new table
        db.create_all()
        
        # Get all hosts
        hosts = Host.query.all()
        total_switches = 0
        
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
            
            # Track previous status to detect changes
            prev_status = None
            switches_created = 0
            
            # Iterate through events chronologically
            for event in events:
                if prev_status is None:
                    prev_status = event.status
                    continue
                
                # If status changed, create a switch
                if event.status != prev_status:
                    switch_type = 'bootup' if event.status == 'online' else 'shutdown'
                    switch = StatusSwitch(
                        host_id=host.id,
                        switch_type=switch_type,
                        timestamp=event.timestamp
                    )
                    db.session.add(switch)
                    switches_created += 1
                
                prev_status = event.status
            
            print(f"Created {switches_created} switches for host {host.id}")
            total_switches += switches_created
            
            # Commit changes for this host
            db.session.commit()
        
        print(f"\nMigration complete! Created {total_switches} status switches.")

if __name__ == '__main__':
    migrate_to_switches()
