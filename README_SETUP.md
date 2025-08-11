# Dairy Milk Collection PWA - Setup Guide

## Quick Start

### Option 1: Double-click to run (Windows)
- Simply double-click `run_server.bat` file
- The PWA will start automatically at http://127.0.0.1:8000

### Option 2: Python script
```bash
python run_server.py
```

### Option 3: Manual commands
```bash
python manage.py migrate
python manage.py runserver
```

## First Time Setup

1. **Install Python** (if not already installed)
   - Download from https://python.org
   - Make sure to check "Add Python to PATH"

2. **Install Django**
   ```bash
   pip install django
   ```

3. **Run the application**
   - Double-click `run_server.bat` OR
   - Run `python run_server.py`

4. **Access the PWA**
   - Open browser and go to: http://127.0.0.1:8000
   - Create a user account to get started

## Default Login
**Superuser Account:**
- Username: `suraj`
- Password: `1234`
- Email: `suraj@dairy.com`

**Alternative:**
- Create your own account through the registration page
- Or manually create superuser: `python manage.py createsuperuser`

## Features
- ✅ Producer Management
- ✅ Milk Collection Tracking
- ✅ Rate Management
- ✅ Financial Deductions
- ✅ Reports & Export
- ✅ Responsive Design

## Troubleshooting
- If port 8000 is busy, the server will automatically use the next available port
- Make sure Python and Django are properly installed
- Check that you're in the correct project directory

## Support
For any issues, check the console output for error messages.