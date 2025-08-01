from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from database import db, ApiKey, UsageLog, AdminUser
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import secrets
import string

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard with statistics"""
    # Get statistics
    total_keys = ApiKey.query.count()
    active_keys = ApiKey.query.filter_by(is_active=True).count()
    total_usage = db.session.query(func.sum(ApiKey.current_usage)).scalar() or 0
    
    # Recent usage logs
    recent_logs = UsageLog.query.order_by(desc(UsageLog.timestamp)).limit(10).all()
    
    # Usage by service
    netflix_usage = db.session.query(func.sum(ApiKey.current_usage)).filter_by(service_type='netflix').scalar() or 0
    chatgpt_usage = db.session.query(func.sum(ApiKey.current_usage)).filter_by(service_type='chatgpt').scalar() or 0
    both_usage = db.session.query(func.sum(ApiKey.current_usage)).filter_by(service_type='both').scalar() or 0
    
    # Keys by service
    netflix_keys = ApiKey.query.filter_by(service_type='netflix').count()
    chatgpt_keys = ApiKey.query.filter_by(service_type='chatgpt').count()
    both_keys = ApiKey.query.filter_by(service_type='both').count()
    
    # Usage over time (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_usage = db.session.query(
        func.date(UsageLog.timestamp).label('date'),
        func.count(UsageLog.id).label('count')
    ).filter(UsageLog.timestamp >= seven_days_ago).group_by(
        func.date(UsageLog.timestamp)
    ).order_by('date').all()
    
    stats = {
        'total_keys': total_keys,
        'active_keys': active_keys,
        'total_usage': total_usage,
        'netflix_usage': netflix_usage,
        'chatgpt_usage': chatgpt_usage,
        'both_usage': both_usage,
        'netflix_keys': netflix_keys,
        'chatgpt_keys': chatgpt_keys,
        'both_keys': both_keys,
        'daily_usage': daily_usage
    }
    
    return render_template('admin/dashboard.html', stats=stats, recent_logs=recent_logs)

@admin_bp.route('/keys')
@login_required
def keys():
    """Manage API keys"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filter options
    service_filter = request.args.get('service', '')
    status_filter = request.args.get('status', '')
    
    query = ApiKey.query
    
    if service_filter:
        query = query.filter_by(service_type=service_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'expired':
        query = query.filter(ApiKey.expires_at < datetime.utcnow())
    elif status_filter == 'exhausted':
        query = query.filter(ApiKey.current_usage >= ApiKey.usage_limit)
    
    keys = query.order_by(desc(ApiKey.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/keys.html', keys=keys, 
                         service_filter=service_filter, status_filter=status_filter)

@admin_bp.route('/keys/create', methods=['GET', 'POST'])
@login_required
def create_key():
    """Create new API key"""
    if request.method == 'POST':
        data = request.get_json()
        
        try:
            # Generate new key
            new_key = ApiKey(
                key=ApiKey.generate_key(),
                service_type=data['service_type'],
                usage_limit=int(data['usage_limit']),
                created_by=current_user.id
            )
            
            # Set expiration if provided
            if data.get('expires_in_days'):
                days = int(data['expires_in_days'])
                new_key.expires_at = datetime.utcnow() + timedelta(days=days)
            
            db.session.add(new_key)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'API key created successfully',
                'key': {
                    'id': new_key.id,
                    'key': new_key.key,
                    'service_type': new_key.service_type,
                    'usage_limit': new_key.usage_limit,
                    'expires_at': new_key.expires_at.isoformat() if new_key.expires_at else None
                }
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 400
    
    return render_template('admin/create_key.html')

@admin_bp.route('/keys/<int:key_id>/toggle', methods=['POST'])
@login_required
def toggle_key(key_id):
    """Toggle key active status"""
    key = ApiKey.query.get_or_404(key_id)
    key.is_active = not key.is_active
    db.session.commit()
    
    status = 'activated' if key.is_active else 'deactivated'
    return jsonify({'success': True, 'message': f'Key {status} successfully'})

@admin_bp.route('/keys/<int:key_id>/delete', methods=['POST'])
@login_required
def delete_key(key_id):
    """Delete API key"""
    key = ApiKey.query.get_or_404(key_id)
    db.session.delete(key)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Key deleted successfully'})

@admin_bp.route('/keys/<int:key_id>/reset-usage', methods=['POST'])
@login_required
def reset_key_usage(key_id):
    """Reset key usage count"""
    key = ApiKey.query.get_or_404(key_id)
    key.current_usage = 0
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Key usage reset successfully'})

@admin_bp.route('/keys/<int:key_id>')
@login_required
def key_details(key_id):
    """View key details and usage logs"""
    key = ApiKey.query.get_or_404(key_id)
    
    # Get usage logs for this key
    page = request.args.get('page', 1, type=int)
    logs = UsageLog.query.filter_by(key_id=key_id).order_by(
        desc(UsageLog.timestamp)
    ).paginate(page=page, per_page=50, error_out=False)
    
    return render_template('admin/key_details.html', key=key, logs=logs)

@admin_bp.route('/usage-logs')
@login_required
def usage_logs():
    """View all usage logs"""
    page = request.args.get('page', 1, type=int)
    service_filter = request.args.get('service', '')
    
    query = UsageLog.query
    
    if service_filter:
        query = query.filter_by(service_used=service_filter)
    
    logs = query.order_by(desc(UsageLog.timestamp)).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('admin/usage_logs.html', logs=logs, service_filter=service_filter)

@admin_bp.route('/bulk-create-keys', methods=['POST'])
@login_required
def bulk_create_keys():
    """Create multiple keys at once"""
    data = request.get_json()
    
    try:
        count = int(data['count'])
        service_type = data['service_type']
        usage_limit = int(data['usage_limit'])
        expires_in_days = data.get('expires_in_days')
        
        if count > 100:  # Limit bulk creation
            return jsonify({'success': False, 'message': 'Cannot create more than 100 keys at once'}), 400
        
        created_keys = []
        
        for _ in range(count):
            new_key = ApiKey(
                key=ApiKey.generate_key(),
                service_type=service_type,
                usage_limit=usage_limit,
                created_by=current_user.id
            )
            
            if expires_in_days:
                days = int(expires_in_days)
                new_key.expires_at = datetime.utcnow() + timedelta(days=days)
            
            db.session.add(new_key)
            created_keys.append(new_key)
        
        db.session.commit()
        
        # Return created keys
        keys_data = []
        for key in created_keys:
            keys_data.append({
                'key': key.key,
                'service_type': key.service_type,
                'usage_limit': key.usage_limit,
                'expires_at': key.expires_at.isoformat() if key.expires_at else None
            })
        
        return jsonify({
            'success': True,
            'message': f'Successfully created {count} keys',
            'keys': keys_data
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@admin_bp.route('/export-keys')
@login_required
def export_keys():
    """Export keys as JSON"""
    service_filter = request.args.get('service', '')
    status_filter = request.args.get('status', '')
    
    query = ApiKey.query
    
    if service_filter:
        query = query.filter_by(service_type=service_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'unused':
        query = query.filter_by(current_usage=0)
    
    keys = query.all()
    
    keys_data = []
    for key in keys:
        keys_data.append({
            'key': key.key,
            'service_type': key.service_type,
            'usage_limit': key.usage_limit,
            'current_usage': key.current_usage,
            'remaining_uses': key.get_remaining_uses(),
            'is_active': key.is_active,
            'created_at': key.created_at.isoformat(),
            'expires_at': key.expires_at.isoformat() if key.expires_at else None
        })
    
    return jsonify({
        'keys': keys_data,
        'total_count': len(keys_data),
        'exported_at': datetime.utcnow().isoformat()
    })

@admin_bp.route('/settings')
@login_required
def settings():
    """Admin settings page"""
    return render_template('admin/settings.html')

@admin_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change admin password"""
    data = request.get_json()
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_user.check_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'New password must be at least 6 characters'}), 400
    
    current_user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})
