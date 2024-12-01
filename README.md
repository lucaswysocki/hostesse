# hostesse

Hostesse is a lightweight application for monitoring host status across your network. It provides real-time monitoring of multiple hosts, with features including:

- Real-time host status monitoring (online/offline)
- Uptime/downtime statistics
- Email notifications for status changes
- Visual status indicators and charts
- Multi-user support with authentication

## Requirements

- Flask
- Flask-SQLAlchemy
- Flask-Login
- ping3
- APScheduler
- Flask-Migrate
- Flask-Mail
- python-dotenv

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd hostesse
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the database:
```bash
python setup_db.py
```

## Configuration

1. Create a `.env` file in the root directory with the following settings (optional):
```
MAIL_SERVER=your-smtp-server
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-email@example.com
```

## Running the Application

1. Start the application:
```bash
python run.py
```

2. Access the application:
   - Local access: http://localhost:5000
   - Network access: http://<your-computer-ip>:5000
   
   To find your computer's IP address:
   - Windows: Run `ipconfig` in Command Prompt
   - Linux/Mac: Run `ifconfig` or `ip addr` in Terminal

## Usage

1. Login with your credentials
2. Add hosts to monitor:
   - Click "Add Host"
   - Enter hostname/IP address
   - Optionally enable email notifications
3. Monitor host status:
   - Cyan status indicates online
   - Gray status indicates offline
   - View uptime statistics and charts
   - Receive notifications for status changes

## Security Notes

- The application is configured to run on your local network only
- Ensure your firewall allows connections on port 5000
- Use strong passwords for user accounts
- In production, disable debug mode by setting `debug=False` in run.py

## Support

For issues or questions, please open an issue in the repository.
