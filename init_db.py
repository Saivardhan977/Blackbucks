from app import app, db, User
from werkzeug.security import generate_password_hash

def init_db():
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if admin user exists, if not create one
        if not User.query.filter_by(username='admin').first():
            hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin = User(username='admin', password_hash=hashed_password)
            db.session.add(admin)
            db.session.commit()
            print("Database initialized with admin user.")
        else:
            print("Database already initialized.")

if __name__ == '__main__':
    init_db()
