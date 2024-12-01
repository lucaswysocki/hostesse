from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
mail = Mail()

# Application Factory

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'  # Change this in production
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Load email configuration
    app.config.from_object('app.config.Config')
    
    # Log email configuration
    logger.debug(f"Mail Server: {app.config.get('MAIL_SERVER')}")
    logger.debug(f"Mail Port: {app.config.get('MAIL_PORT')}")
    logger.debug(f"Mail Use TLS: {app.config.get('MAIL_USE_TLS')}")
    logger.debug(f"Mail Username: {app.config.get('MAIL_USERNAME')}")
    logger.debug(f"Mail Default Sender: {app.config.get('MAIL_DEFAULT_SENDER')}")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.login_view = 'auth.login'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import auth_bp
    app.register_blueprint(auth_bp)

    # Initialize scheduler only in the main process
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        with app.app_context():
            from app.tasks import init_scheduler
            scheduler = init_scheduler(app)
            app.scheduler = scheduler  # Store scheduler instance

    return app
