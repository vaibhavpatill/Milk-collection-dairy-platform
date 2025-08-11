#!/usr/bin/env python
"""
Script to create a superuser for Dairy Milk Collection PWA
"""
import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dairy_pwa.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    username = 'suraj'
    password = '1234'
    email = 'suraj@dairy.com'
    
    print("🔐 Creating superuser...")
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        print(f"✅ Superuser '{username}' already exists!")
        return
    
    # Create superuser
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✅ Superuser created successfully!")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Email: {email}")
        print("🌐 You can now login at: http://127.0.0.1:8000/login/")
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

if __name__ == "__main__":
    create_superuser()