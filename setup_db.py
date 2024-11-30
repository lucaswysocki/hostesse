from app import create_app, db
from app.models import User, Host, HostStatusEvent, StatusSwitch
from werkzeug.security import generate_password_hash
import os

def setup_database():
    app = create_app()
    
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # Create test user
        test_user = User(
            username='admin',
            password=generate_password_hash('admin')
        )
        db.session.add(test_user)
        db.session.commit()
        
        print("Database initialized successfully!")
        print("Test user created - Username: admin, Password: admin")

if __name__ == '__main__':
    setup_database()
