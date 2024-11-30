from app import create_app, db
from app.models import Host, HostStatusEvent, StatusSwitch

def clean_database():
    print("\nCleaning database...")
    app = create_app()
    
    with app.app_context():
        # Get counts before cleaning
        hosts_count = Host.query.count()
        events_count = HostStatusEvent.query.count()
        switches_count = StatusSwitch.query.count()
        
        print(f"\nBefore cleaning:")
        print(f"Hosts: {hosts_count}")
        print(f"Status Events: {events_count}")
        print(f"Status Switches: {switches_count}")
        
        # Reset all hosts to unknown status
        Host.query.update({Host.status: 'unknown'})
        
        # Delete all status events and switches
        HostStatusEvent.query.delete()
        StatusSwitch.query.delete()
        
        # Commit changes
        db.session.commit()
        
        # Get counts after cleaning
        hosts_count = Host.query.count()
        events_count = HostStatusEvent.query.count()
        switches_count = StatusSwitch.query.count()
        
        print(f"\nAfter cleaning:")
        print(f"Hosts: {hosts_count}")
        print(f"Status Events: {events_count}")
        print(f"Status Switches: {switches_count}")
        print("\nDatabase cleaned successfully!")

if __name__ == '__main__':
    clean_database()
