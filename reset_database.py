import os
from app import app, db
from models import User, Message

def reset_database():
    with app.app_context():
        # Delete the database file if it exists
        db_path = os.path.join('instance', 'chatbot.db')
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"Removed existing database at {db_path}")
            except Exception as e:
                print(f"Error removing database: {e}")
                return
        
        # Create all tables
        try:
            db.create_all()
            print("Created new database tables")
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created admin user with username 'admin' and password 'admin123'")
            
            print("Database reset successful!")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()

if __name__ == '__main__':
    reset_database()
