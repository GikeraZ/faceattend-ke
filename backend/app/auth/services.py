"""Authentication service layer"""
from datetime import datetime
import re
from ..extensions import db
from ..models import User


def validate_registration(data):
    """Validate registration data with Kenya-specific rules"""
    errors = {}
    
    # Registration number format: XX-YYYY-NNNNN (e.g., CS-2024-00123)
    reg_pattern = r'^[A-Z]{2,4}-\d{4}-\d{5,6}$'
    if not data.get('reg_number') or not re.match(reg_pattern, data['reg_number']):
        errors['reg_number'] = 'Invalid format. Use: CS-2024-00123'
    
    # Email validation
    email = data.get('email', '')
    if not email or '@' not in email:
        errors['email'] = 'Valid email required'
    elif not email.endswith('.ac.ke') and not email.endswith('.ke'):
        # Warn but allow non-.ac.ke emails for flexibility
        pass
    
    # Password strength
    password = data.get('password', '')
    if len(password) < 8:
        errors['password'] = 'Minimum 8 characters required'
    elif not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password):
        errors['password'] = 'Must include uppercase and lowercase letters'
    elif not re.search(r'\d', password):
        errors['password'] = 'Must include at least one number'
    
    # Phone (Kenyan format)
    phone = data.get('phone', '')
    if phone and not re.match(r'^\+254\d{9}$', phone):
        errors['phone'] = 'Use Kenyan format: +2547XXXXXXXX'
    
    # Consent required
    consent = data.get('consent', {})
    if not consent.get('biometric_processing'):
        errors['consent.biometric_processing'] = 'Required for face recognition'
    
    return errors


def create_user(reg_number, email, password, full_name, phone=None, 
                role='student', consent_data=None, ip_address=None):
    """Create new user with consent tracking"""
    # Check for duplicates
    if User.query.filter_by(reg_number=reg_number).first():
        raise ValueError('Registration number already exists')
    if User.query.filter_by(email=email).first():
        raise ValueError('Email already registered')
    
    # Create user
    user = User(
        reg_number=reg_number,
        email=email,
        full_name=full_name,
        phone=phone,
        role=role
    )
    user.set_password(password)
    
    # Record consent if provided
    if consent_data and consent_data.get('biometric_processing'):
        user.give_consent(ip_address=ip_address)
    
    db.session.add(user)
    db.session.commit()
    
    return user