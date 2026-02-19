"""FaceAttend-KE Flask Application Factory"""
import os
import pymysql
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Import config BEFORE using it
from .config import Config
from .extensions import db, login_manager, migrate, limiter
from .auth.routes import auth_bp
from .face.routes import face_bp
from .attendance.routes import attendance_bp
from .compliance.routes import compliance_bp

# Register PyMySQL as MySQLdb replacement
pymysql.install_as_MySQLdb()


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__, instance_relative_config=True)
    
    # Set secret key BEFORE initializing extensions
    app.config['SECRET_KEY'] = os.getenv(
        'SECRET_KEY', 
        'dev-key-change-in-production-xyz123-abc456-def789'
    )
    
    # Load config
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # ✅ ADD THIS: User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from .models import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(face_bp, url_prefix='/api/face')
    app.register_blueprint(attendance_bp, url_prefix='/api/attendance')
    app.register_blueprint(compliance_bp, url_prefix='/api/compliance')
    
    # Health check endpoint
    @app.route('/api/health')
    @limiter.exempt
    def health_check():
        return jsonify({'status': 'healthy', 'version': '1.0.0'}), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    return app