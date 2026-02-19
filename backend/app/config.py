"""Application configuration with all required settings"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration - ALL required settings"""
    
    # ==================== SECURITY ====================
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production-xyz123-abc456-def789')
    
    # ==================== DATABASE ====================
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'mysql://root:@localhost:3306/faceattend_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # ==================== FACE RECOGNITION ====================
    FACE_TOLERANCE = float(os.getenv('FACE_TOLERANCE', '0.6'))
    FACE_ENCODING_MODEL = os.getenv('FACE_MODEL', 'small')  # ✅ ADDED - This was missing!
    MAX_IMAGE_SIZE_MB = int(os.getenv('MAX_IMAGE_SIZE_MB', '5'))
    
    # ==================== RATE LIMITING ====================
    RATELIMIT_DEFAULT = "100 per hour"
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    
    # ==================== SESSION ====================
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = os.getenv('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # ==================== KENYA COMPLIANCE ====================
    TIMEZONE = 'Africa/Nairobi'
    DATA_RETENTION_YEARS = int(os.getenv('DATA_RETENTION_YEARS', '6'))
    DPO_EMAIL = os.getenv('DPO_EMAIL', 'dpo@institution.ac.ke')
    CONSENT_POLICY_VERSION = os.getenv('CONSENT_VERSION', '1.0')
    
    # ==================== EMAIL (SMTP) ====================
    MAIL_SERVER = os.getenv('SMTP_SERVER')
    MAIL_PORT = int(os.getenv('SMTP_PORT', '587'))
    MAIL_USE_TLS = os.getenv('SMTP_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('SMTP_USER')
    MAIL_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # ==================== SMS (Africa's Talking) ====================
    AFRICAS_TALKING_USERNAME = os.getenv('AT_USERNAME')
    AFRICAS_TALKING_API_KEY = os.getenv('AT_API_KEY')


class DevelopmentConfig(Config):
    """Development settings"""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production settings"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True


# Config dictionary for app factory
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}