from app import create_app, db
from app.models import HostStatusEvent
from datetime import datetime

app = create_app()

with app.app_context():
    events = HostStatusEvent.query.order_by(HostStatusEvent.timestamp.asc()).all()
    print("\nAll status events (chronological order):")
    print("=" * 60)
    print(f"{'Timestamp':<25} {'Status':<10} {'Host ID'}")
    print("-" * 60)
    for event in events:
        print(f"{event.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<25} {event.status:<10} {event.host_id}")
    print("=" * 60)
