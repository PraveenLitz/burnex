from app import app, db, User

# 1. Reset Database First (Because we added is_admin column)
print("Resetting Database Schema...")
with app.app_context():
    db.drop_all()
    db.create_all()
    print("Database Reset Complete.")

    # 2. Create the Admin User
    print("Creating Admin User...")
    from werkzeug.security import generate_password_hash
    
    # CHANGE THESE DETAILS
    admin_email = "admin@nutriscan.com"
    admin_pass = "admin123"
    
    admin = User(
        username="SuperAdmin",
        email=admin_email,
        password=generate_password_hash(admin_pass, method='pbkdf2:sha256'),
        is_admin=True,  # Crucial
        is_premium=True # Admins get premium features
    )
    
    db.session.add(admin)
    db.session.commit()
    
    print(f"Admin Created! Login with: {admin_email} / {admin_pass}")