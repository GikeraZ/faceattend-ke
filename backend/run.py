#!/usr/bin/env python3
"""Application entry point"""
import os
import sys
from app import create_app
from app.extensions import db
from app.models import User, Course

app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Add models to flask shell"""
    return {'db': db, 'User': User, 'Course': Course}


@app.cli.command('init-db')
def init_db():
    """Initialize database with tables and sample data"""
    with app.app_context():
        db.create_all()
        
        # Create sample instructor if none exists
        if not User.query.filter_by(role='instructor').first():
            from werkzeug.security import generate_password_hash
            
            instructor = User(
                reg_number='INST-001',
                email='instructor@demo.ac.ke',
                full_name='Demo Instructor',
                role='instructor',
                consent_given=True
            )
            instructor.password_hash = generate_password_hash('instructor123')
            db.session.add(instructor)
            
            # Create sample course
            course = Course(
                code='CS301',
                name='Advanced Software Engineering',
                department='Computer Science',
                instructor_id=instructor.id
            )
            db.session.add(course)
            
            # Create sample student
            student = User(
                reg_number='CS-2024-001',
                email='student@demo.ac.ke',
                full_name='Demo Student',
                role='student',
                consent_given=True
            )
            student.password_hash = generate_password_hash('student123')
            db.session.add(student)
            
            db.session.commit()
            print("✅ Sample data created:")
            print("   Instructor: INST-001 / instructor123")
            print("   Student: CS-2024-001 / student123")
            print("   Course: CS301")
        
        print("✅ Database initialized")


if __name__ == '__main__':
    # Development server
    if len(sys.argv) == 1:
        app.run(host='0.0.0.0', port=8000, debug=True)
    else:
        # Let gunicorn or other WSGI server handle
        pass