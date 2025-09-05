from app import app, db, User

def init_database():
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Check if admin user exists, if not create one
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Database initialized with admin user.")
        else:
            print("Database already initialized.")

if __name__ == '__main__':
    init_database()
