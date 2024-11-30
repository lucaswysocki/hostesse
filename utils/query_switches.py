from app import create_app, db
from app.models import StatusSwitch
from datetime import datetime

app = create_app()

with app.app_context():
    switches = StatusSwitch.query.order_by(StatusSwitch.timestamp.asc()).all()
    print("\nAll status switches (chronological order):")
    print("=" * 60)
    print(f"{'Timestamp':<25} {'Type':<10} {'Host ID'}")
    print("-" * 60)
    for switch in switches:
        print(f"{switch.timestamp.strftime('%Y-%m-%d %H:%M:%S'):<25} {switch.switch_type:<10} {switch.host_id}")
    print("=" * 60)
