"""Database setup script"""
from app import create_app
from app.extensions import db
from app.models import User, Course
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Create all tables
    db.create_all()
    print("✅ Tables created successfully!")
    
    # Create sample instructor if none exists
    if not User.query.filter_by(role='instructor').first():
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
    
    print("✅ Database setup complete!")