#!/usr/bin/env python3
"""
Setup script for WordFlow Django Blog
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_project():
    """Setup the WordFlow project"""
    print("🚀 Setting up WordFlow Django Blog...")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
    django.setup()
    
    try:
        # Run migrations
        print("📦 Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        # Create superuser if needed
        print("👤 Creating superuser (optional)...")
        print("You can skip this step and create a superuser later with: python manage.py createsuperuser")
        
        # Collect static files
        print("📁 Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        
        print("✅ Setup completed successfully!")
        print("\n🎉 WordFlow is ready to use!")
        print("Run: python manage.py runserver")
        print("Then visit: http://127.0.0.1:8000")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == '__main__':
    setup_project()
