from flask import render_template, redirect, url_for, flash, request, Blueprint, jsonify, session
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from . import db
from .models import Host, User, HostStatusEvent, StatusSwitch
from . import login_manager
import ping3
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create a Blueprint for routes
auth_bp = Blueprint('auth', __name__)

# Home route
@auth_bp.route('/')
@login_required
def index():
    hosts = Host.query.all()
    for host in hosts:
        response = ping3.ping(host.ip_address, timeout=1)
        if response:
            host.status = 'online'
            logging.debug(f"Host {host.ip_address} is online.")
        else:
            host.status = 'offline'
            logging.debug(f"Host {host.ip_address} is offline.")
        db.session.commit()
    return render_template('index.html', hosts=hosts)

# Add host route
@auth_bp.route('/add_host', methods=['POST'])
@login_required
def add_host():
    hostname = request.form.get('hostname')
    ip_address = request.form.get('ip_address')
    if ip_address:
        new_host = Host(hostname=hostname, ip_address=ip_address, status='offline')
        db.session.add(new_host)
        db.session.commit()
        flash('Host added successfully!', 'success')
    return redirect(url_for('auth.index'))

# Remove host route
@auth_bp.route('/remove_host/<int:host_id>')
@login_required
def remove_host(host_id):
    host = Host.query.get_or_404(host_id)
    
    # First delete all associated status switches
    StatusSwitch.query.filter_by(host_id=host_id).delete()
    
    # Then delete all associated status events
    HostStatusEvent.query.filter_by(host_id=host_id).delete()
    
    # Finally delete the host
    db.session.delete(host)
    db.session.commit()
    
    flash('Host removed successfully!', 'success')
    return redirect(url_for('auth.index'))

# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing messages when accessing login page
    if request.method == 'GET':
        session.clear()
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('auth.index'))
        
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

# Logout route
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    # Clear any existing flash messages
    session = request.environ.get('beaker.session')
    if session:
        session.clear()
    return redirect(url_for('auth.login'))

# Host statistics API endpoint
@auth_bp.route('/api/host/<int:host_id>/stats')
@login_required
def host_stats(host_id):
    host = Host.query.get_or_404(host_id)
    return jsonify(host.get_status_statistics())

# Notification routes
@auth_bp.route('/api/notifications')
@login_required
def get_notifications():
    unread_notifications = StatusSwitch.query.filter_by(is_read=False)\
        .order_by(StatusSwitch.timestamp.desc())\
        .limit(20)\
        .all()
    return jsonify([notification.to_dict() for notification in unread_notifications])

@auth_bp.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    notification_ids = request.json.get('notification_ids', [])
    if notification_ids:
        StatusSwitch.query.filter(StatusSwitch.id.in_(notification_ids))\
            .update({StatusSwitch.is_read: True}, synchronize_session=False)
        db.session.commit()
    return jsonify({'status': 'success'})

@auth_bp.route('/api/notifications/count')
@login_required
def get_notification_count():
    count = StatusSwitch.query.filter_by(is_read=False).count()
    return jsonify({'count': count})
