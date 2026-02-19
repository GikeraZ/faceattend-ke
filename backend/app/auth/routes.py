"""Authentication routes: register, login, logout, consent"""
from flask import request, jsonify, current_app
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from ..extensions import db, limiter
from ..models import User, ConsentRecord
from ..compliance.audit import log_audit
from . import auth_bp


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    """Register new user with academic information"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Check required fields
        required = ['reg_number', 'email', 'password', 'full_name', 'course_program']
        for field in required:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check consent
        consent = data.get('consent', {})
        if not consent.get('biometric_processing'):
            return jsonify({'error': 'Biometric consent is required'}), 400
        
        if not consent.get('data_storage'):
            return jsonify({'error': 'Data storage consent is required'}), 400
        
        # Check if user exists
        if User.query.filter_by(reg_number=data['reg_number']).first():
            return jsonify({'error': 'Registration number already exists'}), 409
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create user with academic info and role support
        from werkzeug.security import generate_password_hash
        
        user = User(
            reg_number=data['reg_number'],
            email=data['email'],
            full_name=data['full_name'],
            phone=data.get('phone'),
            year_of_study=data.get('year_of_study'),  # For students
            course_program=data['course_program'],
            role=data.get('role', 'student'),  # ✅ Support lecturer/instructor role
            consent_given=True
        )
        user.password_hash = generate_password_hash(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Log consent
        consent_log = ConsentRecord(
            user_id=user.id,
            consent_type='biometric_processing',
            action='given',
            new_value=True,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            policy_version=current_app.config.get('CONSENT_POLICY_VERSION', '1.0')
        )
        db.session.add(consent_log)
        db.session.commit()
        
        # Audit
        log_audit(
            actor_id=user.id,
            action='user_registered',
            resource_type='user',
            resource_id=user.id,
            ip_address=request.remote_addr,
            status_code=201
        )
        
        return jsonify({
            'message': 'Registration successful! Please login.',
            'user_id': user.id,
            'role': user.role
        }), 201
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 409
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Authenticate user"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No credentials provided'}), 400
    
    identifier = data.get('reg_number') or data.get('email')
    password = data.get('password')
    
    if not identifier or not password:
        return jsonify({'error': 'Registration number/email and password required'}), 400
    
    user = User.query.filter(
        (User.reg_number == identifier) | (User.email == identifier)
    ).first()
    
    if user and user.check_password(password) and user.is_active:
        login_user(user)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        log_audit(
            actor_id=user.id,
            action='login_success',
            resource_type='session',
            ip_address=request.remote_addr,
            status_code=200
        )
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(include_sensitive=True),
            'role': user.role
        }), 200
    
    # Audit failed attempt
    log_audit(
        action='login_failed',
        resource_type='auth',
        ip_address=request.remote_addr,
        status_code=401,
        error_message='Invalid credentials'
    )
    
    return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    if current_user.is_authenticated:
        user_id = current_user.id
        logout_user()
        
        log_audit(
            actor_id=user_id,
            action='logout',
            resource_type='session',
            status_code=200
        )
    
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user profile"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify(current_user.to_dict(include_sensitive=True)), 200


@auth_bp.route('/consent', methods=['GET', 'PUT'])
@login_required
def manage_consent():
    """View or update consent preferences"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
    
    if request.method == 'GET':
        records = ConsentRecord.query.filter_by(user_id=current_user.id).order_by(ConsentRecord.timestamp.desc()).all()
        
        return jsonify({
            'current_consent': {
                'biometric_processing': current_user.consent_given,
                'version': current_user.consent_version,
                'timestamp': current_user.consent_timestamp.isoformat() if current_user.consent_timestamp else None
            },
            'history': [r.to_dict() for r in records]
        }), 200
    
    # PUT: Update consent
    data = request.get_json()
    
    if data.get('biometric_processing') is False and current_user.consent_given:
        current_user.consent_given = False
        current_user.face_encoding = None
        current_user.face_enrolled_at = None
        
        consent_log = ConsentRecord(
            user_id=current_user.id,
            consent_type='biometric_processing',
            action='withdrawn',
            previous_value=True,
            new_value=False,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            policy_version=current_app.config.get('CONSENT_POLICY_VERSION', '1.0'),
            reason=data.get('reason', 'User requested withdrawal')
        )
        db.session.add(consent_log)
        db.session.commit()
        
        log_audit(
            actor_id=current_user.id,
            action='consent_withdrawn',
            resource_type='consent',
            ip_address=request.remote_addr,
            status_code=200
        )
    
    return jsonify({
        'message': 'Consent updated',
        'consent_status': current_user.consent_given
    }), 200