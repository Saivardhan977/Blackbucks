import os
from app import app, db

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        
        # Create all tables
        db.create_all()
        
        # If you have any initial data to add, you can add it here
        # For example, adding a default user
        from models import User
        from werkzeug.security import generate_password_hash
        
        # Create a default user (change these credentials in production!)
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin')
            )
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user with username 'admin' and password 'admin'")

if __name__ == '__main__':
    reset_database()
    print("Database has been reset successfully!")
