"""SQLAlchemy models with academic information"""
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(UserMixin, db.Model):
    """User model - students, instructors, admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    reg_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    
    # ✅ Academic Information
    year_of_study = db.Column(db.String(20), nullable=True)  # Year 1, Year 2, etc.
    course_program = db.Column(db.String(100), nullable=True)  # Computer Science, IT, etc.
    
    # Consent tracking (Data Protection Act 2019)
    consent_given = db.Column(db.Boolean, default=False)
    consent_timestamp = db.Column(db.DateTime)
    consent_ip = db.Column(db.String(45))
    consent_version = db.Column(db.String(10), default='1.0')
    
    # Face biometrics (stored as encoding vector, NOT raw image)
    face_encoding = db.Column(db.PickleType, nullable=True)
    face_enrolled_at = db.Column(db.DateTime)
    
    # Metadata
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship(
        'Attendance',
        foreign_keys='Attendance.user_id',
        backref='student',
        lazy='dynamic'
    )
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def give_consent(self, ip_address, version='1.0'):
        """Record explicit consent per Data Protection Act"""
        self.consent_given = True
        self.consent_timestamp = datetime.utcnow()
        self.consent_ip = ip_address
        self.consent_version = version
        return self
    
    def withdraw_consent(self):
        """Allow user to withdraw consent"""
        self.consent_given = False
        self.face_encoding = None
        self.face_enrolled_at = None
        return self
    
    def to_dict(self, include_sensitive=False):
        """Serialize user for API responses"""
        data = {
            'id': self.id,
            'reg_number': self.reg_number,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'year_of_study': self.year_of_study,
            'course_program': self.course_program,
            'consent_status': {
                'given': self.consent_given,
                'version': self.consent_version,
                'timestamp': self.consent_timestamp.isoformat() if self.consent_timestamp else None
            },
            'face_enrolled': self.face_encoding is not None,
            'created_at': self.created_at.isoformat()
        }
        if include_sensitive and self.role in ['admin', 'instructor']:
            data['phone'] = self.phone
            data['last_login'] = self.last_login.isoformat() if self.last_login else None
        return data
    
    def __repr__(self):
        return f'<User {self.reg_number}>'


class Course(db.Model):
    """Course/Unit model"""
    __tablename__ = 'courses'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='course', lazy='dynamic')
    instructor = db.relationship('User', foreign_keys=[instructor_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'department': self.department,
            'instructor': self.instructor.full_name if self.instructor else None
        }


class Attendance(db.Model):
    """Attendance record with compliance metadata"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    
    # Timestamp with Kenya timezone
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Location data (optional GPS validation)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_accuracy = db.Column(db.Float)
    
    # Face recognition metadata
    confidence_score = db.Column(db.Float)
    match_method = db.Column(db.String(30), default='face_recognition')
    liveness_verified = db.Column(db.Boolean, default=False)
    
    # Academic info at time of attendance
    year_of_study = db.Column(db.String(20))
    course_program = db.Column(db.String(100))
    unit_code = db.Column(db.String(20))
    
    # Status and audit
    status = db.Column(db.String(20), default='present')
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    
    # Compliance
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    verifier = db.relationship('User', foreign_keys=[verified_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'student': {
                'id': self.student.id,
                'reg_number': self.student.reg_number,
                'full_name': self.student.full_name
            } if self.student else None,
            'course': self.course.to_dict() if self.course else None,
            'timestamp': self.timestamp.isoformat(),
            'year_of_study': self.year_of_study,
            'course_program': self.course_program,
            'unit_code': self.unit_code or (self.course.code if self.course else None),
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'accuracy': self.location_accuracy
            } if self.latitude else None,
            'confidence': self.confidence_score,
            'liveness_verified': self.liveness_verified,
            'status': self.status,
            'method': self.match_method
        }


class ConsentRecord(db.Model):
    """Audit trail for consent changes"""
    __tablename__ = 'consent_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    consent_type = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(20), nullable=False)
    previous_value = db.Column(db.Boolean)
    new_value = db.Column(db.Boolean, nullable=False)
    
    # Context
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    policy_version = db.Column(db.String(10))
    reason = db.Column(db.Text)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='consent_history')
    
    def to_dict(self):
        return {
            'id': self.id,
            'consent_type': self.consent_type,
            'action': self.action,
            'timestamp': self.timestamp.isoformat(),
            'policy_version': self.policy_version
        }


class AuditLog(db.Model):
    """Immutable audit log for compliance"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Action details
    action = db.Column(db.String(50), nullable=False, index=True)
    resource_type = db.Column(db.String(30))
    resource_id = db.Column(db.Integer)
    
    # Request context
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    request_method = db.Column(db.String(10))
    request_path = db.Column(db.String(255))
    
    # Result
    status_code = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    
    # Biometric-specific fields
    face_match_confidence = db.Column(db.Float)
    liveness_score = db.Column(db.Float)
    
    # Immutable timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    actor = db.relationship('User', backref='audit_logs_actor', foreign_keys=[actor_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'resource': f"{self.resource_type}:{self.resource_id}",
            'actor': self.actor.reg_number if self.actor else 'system',
            'timestamp': self.timestamp.isoformat(),
            'ip': self.ip_address,
            'status': self.status_code
        }