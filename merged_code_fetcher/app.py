from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from merged_code_fetcher.database import db, init_db, create_sample_keys, AdminUser, ApiKey, UsageLog
from merged_code_fetcher.admin import admin_bp
from merged_code_fetcher.email_reader import get_latest_netflix_code, get_latest_chatgpt_code
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///code_fetcher.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = 'Please log in to access the admin panel.'

@login_manager.user_loader
def load_user(user_id):
    return AdminUser.query.get(int(user_id))

# Initialize database
init_db(app)

# Register blueprints
app.register_blueprint(admin_bp)

# Create sample data on first run
with app.app_context():
    create_sample_keys()

@app.route('/')
def index():
    """Main page with service selection"""
    return render_template('index.html')

@app.route('/netflix')
def netflix_page():
    """Netflix code fetcher page"""
    return render_template('netflix.html')

@app.route('/chatgpt')
def chatgpt_page():
    """ChatGPT code fetcher page"""
    return render_template('chatgpt.html')

@app.route('/get-code', methods=['POST'])
def get_code():
    """Get verification code for specified service"""
    data = request.json
    user_key = data.get('key')
    service = data.get('service', 'netflix')  # Default to netflix for backward compatibility
    
    if not user_key:
        return jsonify({'error': 'Key is required'}), 400
    
    if service not in ['netflix', 'chatgpt']:
        return jsonify({'error': 'Invalid service specified'}), 400
    
    # Find the API key
    api_key = ApiKey.query.filter_by(key=user_key).first()
    if not api_key:
        return jsonify({'error': 'Invalid key provided'}), 403
    
    # Check if key is valid
    is_valid, message = api_key.is_valid()
    if not is_valid:
        return jsonify({'error': message}), 403
    
    # Check if key can be used for this service
    if not api_key.can_use_service(service):
        return jsonify({'error': f'Key is not valid for {service} service'}), 403
    
    # Get the appropriate code
    try:
        if service == 'netflix':
            code = get_latest_netflix_code()
        else:  # chatgpt
            code = get_latest_chatgpt_code()
        
        if code and not code.startswith('Error') and not code.startswith('No'):
            # Increment usage and log
            api_key.increment_usage(service, request.remote_addr)
            
            return jsonify({
                'code': code, 
                'success': True,
                'remaining_uses': api_key.get_remaining_uses()
            })
        else:
            # Log failed attempt
            usage_log = UsageLog(
                key_id=api_key.id,
                service_used=service,
                ip_address=request.remote_addr,
                success=False,
                error_message=code or 'No code found'
            )
            db.session.add(usage_log)
            db.session.commit()
            
            return jsonify({'error': f'No recent {service} code found'}), 404
            
    except Exception as e:
        # Log error
        usage_log = UsageLog(
            key_id=api_key.id,
            service_used=service,
            ip_address=request.remote_addr,
            success=False,
            error_message=str(e)
        )
        db.session.add(usage_log)
        db.session.commit()
        
        return jsonify({'error': f'Error fetching {service} code: {str(e)}'}), 500

@app.route('/validate-key', methods=['POST'])
def validate_key():
    """Real-time key validation endpoint"""
    data = request.json
    user_key = data.get('key')
    service = data.get('service', 'netflix')
    
    if not user_key:
        return jsonify({'valid': False, 'message': 'Key is required'})
    
    # Find the API key
    api_key = ApiKey.query.filter_by(key=user_key).first()
    if not api_key:
        return jsonify({'valid': False, 'message': 'Invalid key'})
    
    # Check if key is valid
    is_valid, message = api_key.is_valid()
    if not is_valid:
        return jsonify({'valid': False, 'message': message})
    
    # Check if key can be used for this service
    if not api_key.can_use_service(service):
        return jsonify({'valid': False, 'message': f'Key not valid for {service} service'})
    
    return jsonify({
        'valid': True, 
        'message': f'Valid key - {api_key.get_remaining_uses()} uses remaining',
        'remaining_uses': api_key.get_remaining_uses(),
        'service_type': api_key.service_type
    })

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = AdminUser.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout"""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/api/stats')
def api_stats():
    """Public API stats endpoint"""
    total_keys = ApiKey.query.count()
    active_keys = ApiKey.query.filter_by(is_active=True).count()
    total_usage = db.session.query(db.func.sum(ApiKey.current_usage)).scalar() or 0
    
    return jsonify({
        'total_keys': total_keys,
        'active_keys': active_keys,
        'total_usage': total_usage,
        'services': ['netflix', 'chatgpt']
    })

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

@app.context_processor
def inject_current_year():
    """Inject current year into all templates"""
    return {'current_year': datetime.now().year}

app = Flask(__name__)  # and later, exposed as `app`
