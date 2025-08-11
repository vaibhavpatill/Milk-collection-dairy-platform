#!/usr/bin/env python
"""
Simple script to run the Dairy Milk Collection PWA
"""
import os
import sys
import subprocess

def run_server():
    print("🐄 Starting Dairy Milk Collection PWA...")
    print("=" * 50)
    
    # Check if Django is installed
    try:
        import django
        print(f"✅ Django {django.get_version()} found")
    except ImportError:
        print("❌ Django not found. Please install Django:")
        print("   pip install django")
        return
    
    # Run migrations first
    print("\n📦 Running database migrations...")
    try:
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        print("✅ Database migrations completed")
    except subprocess.CalledProcessError:
        print("❌ Migration failed")
        return
    
    # Create superuser
    print("\n👤 Creating superuser...")
    try:
        subprocess.run([sys.executable, "create_superuser.py"], check=True)
    except subprocess.CalledProcessError:
        print("⚠️ Superuser creation failed (may already exist)")
    
    # Add sample data if database is empty
    print("\n📊 Checking for sample data...")
    try:
        subprocess.run([sys.executable, "-c", 
            "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dairy_pwa.settings'); django.setup(); from core.models import MilkProducer; print('Sample data exists' if MilkProducer.objects.exists() else 'No data'); exit(0 if MilkProducer.objects.exists() else 1)"], 
            check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("📊 Adding sample data...")
        try:
            subprocess.run([sys.executable, "add_sample_data.py"], check=True)
            subprocess.run([sys.executable, "add_deductions.py"], check=True)
            print("✅ Sample data added successfully")
        except subprocess.CalledProcessError:
            print("⚠️ Sample data creation failed")
    
    # Start the development server
    print("\n🚀 Starting development server...")
    print("📱 Access your PWA at: http://127.0.0.1:8000")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        subprocess.run([sys.executable, "manage.py", "runserver"])
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Thank you for using Dairy PWA!")

if __name__ == "__main__":
    run_server()