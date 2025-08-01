#!/usr/bin/env python3
"""
Initialize the Merged Code Fetcher application
This script sets up the database and creates the initial admin user
"""

import os
import sys
from dotenv import load_dotenv
from database import db, ApiKey, AdminUser
from app import app
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize the database with tables and initial data"""
    print("Initializing database...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully")
        
        # Check if admin user exists
        admin = AdminUser.query.first()
        if not admin:
            # Create default admin user
            admin = AdminUser(username='admin')
            admin.set_password('admin123')  # Default password - CHANGE IN PRODUCTION
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created (username: admin, password: admin123)")
        else:
            print("Admin user already exists")
        
        # Check if any API keys exist
        if ApiKey.query.count() == 0:
            print("No API keys found. You can create keys in the admin panel.")
        else:
            print(f"Found {ApiKey.query.count()} existing API keys")

def main():
    """Main initialization function"""
    print("Merged Code Fetcher Initialization Script")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    print("Environment variables loaded")
    
    # Initialize database
    init_database()
    
    print("\nInitialization complete!")
    print("\nNext steps:")
    print("1. Run the application: python app.py")
    print("2. Visit http://localhost:5000 to access the user interface")
    print("3. Visit http://localhost:5000/admin to access the admin panel")
    print("4. Log in with username: admin, password: admin123")
    print("5. Change the default admin password immediately!")

if __name__ == '__main__':
    main()
