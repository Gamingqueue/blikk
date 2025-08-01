from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string

db = SQLAlchemy()

class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<AdminUser {self.username}>'

class ApiKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False)
    service_type = db.Column(db.String(20), nullable=False)  # 'netflix', 'chatgpt', or 'both'
    usage_limit = db.Column(db.Integer, nullable=False, default=1)
    current_usage = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=False)
    
    # Relationships
    usage_logs = db.relationship('UsageLog', backref='api_key', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('AdminUser', backref='created_keys')
    
    @staticmethod
    def generate_key():
        """Generate a random API key"""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(16))
    
    def is_valid(self):
        """Check if key is valid for use"""
        if not self.is_active:
            return False, "Key is inactive"
        
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False, "Key has expired"
        
        if self.current_usage >= self.usage_limit:
            return False, "Usage limit exceeded"
        
        return True, "Valid"
    
    def can_use_service(self, service):
        """Check if key can be used for specific service"""
        return self.service_type == 'both' or self.service_type == service
    
    def increment_usage(self, service, ip_address=None):
        """Increment usage count and log the usage"""
        self.current_usage += 1
        
        # Create usage log
        usage_log = UsageLog(
            key_id=self.id,
            service_used=service,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        db.session.add(usage_log)
        db.session.commit()
    
    def get_remaining_uses(self):
        """Get remaining uses for this key"""
        return max(0, self.usage_limit - self.current_usage)
    
    def __repr__(self):
        return f'<ApiKey {self.key[:8]}... ({self.service_type})>'

class UsageLog(db.Model):
    __tablename__ = 'usage_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    key_id = db.Column(db.Integer, db.ForeignKey('api_keys.id'), nullable=False)
    service_used = db.Column(db.String(20), nullable=False)  # 'netflix' or 'chatgpt'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 can be up to 45 chars
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<UsageLog {self.service_used} at {self.timestamp}>'

def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # Create default admin user if none exists
        if not AdminUser.query.first():
            admin = AdminUser(username='admin')
            admin.set_password('admin123')  # Change this in production!
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user: admin/admin123")

def create_sample_keys():
    """Create some sample keys for testing"""
    admin = AdminUser.query.first()
    if admin and ApiKey.query.count() == 0:
        # Create sample keys
        sample_keys = [
            {'service': 'netflix', 'limit': 5},
            {'service': 'chatgpt', 'limit': 3},
            {'service': 'both', 'limit': 10},
        ]
        
        for key_data in sample_keys:
            key = ApiKey(
                key=ApiKey.generate_key(),
                service_type=key_data['service'],
                usage_limit=key_data['limit'],
                created_by=admin.id,
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(key)
        
        db.session.commit()
        print("Created sample API keys")
