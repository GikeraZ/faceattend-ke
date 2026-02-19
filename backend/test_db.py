from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    try:
        # Test connection
        db.engine.connect()
        print("✅ Database connection successful!")
        
        # Check tables
        tables = db.metadata.tables.keys()
        print(f"📋 Tables found: {list(tables)}")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")