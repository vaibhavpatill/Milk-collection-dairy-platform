# Dairy Milk Collection PWA

This is a Progressive Web App (PWA) for managing milk collection at a dairy, built with Django, HTML, CSS, and JavaScript.

## Features
- User authentication for staff (Django built-in)
- Milk producer registration (name, date, unique ID)
- Milk collection form (producer lookup, milk type, litres, fat, SNF, rate, total)
- Milk rate management (rate charts for buffalo/cow by fat value)
- 10-day billing system (summary, deductions, net payable)
- Reports/dashboard (history, filters, export)
- PWA features: offline access, installable (service worker, manifest.json)
- Responsive design (Bootstrap optional)

## Technologies
- Backend: Python (Django)
- Frontend: HTML, CSS, JavaScript
- Database: SQLite (default)
- PWA: Service Worker, manifest.json

## Local Development
1. Install Python 3.x and pip
2. Install Django: `pip install django`
3. Run server: `python manage.py runserver`
4. Access app at: http://localhost:8000

## Setup
- All code is in the `dairy_pwa` Django project folder.
- Follow comments in code for further setup and customization.

## Next Steps
- Implement models, views, templates, and static files as per requirements.
- Add service worker and manifest.json for PWA functionality.
- See copilot-instructions.md for workspace-specific guidance.
