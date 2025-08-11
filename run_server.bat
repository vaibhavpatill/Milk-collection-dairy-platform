@echo off
echo 🐄 Starting Dairy Milk Collection PWA...
echo ==================================================

echo 📦 Running database migrations...
python manage.py migrate

echo.
echo Creating superuser...
python create_superuser.py

echo.
echo 🚀 Starting development server...
echo 📱 Access your PWA at: http://127.0.0.1:8000
echo 🛑 Press Ctrl+C to stop the server
echo ==================================================

python manage.py runserver

pause