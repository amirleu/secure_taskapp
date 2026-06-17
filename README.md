# Secure Task Management Application
### IKB21503 Secure Software Development — UniKL MIIT

## Project Description
A secure web application built with Django implementing OWASP Top 10 
security controls, Role-Based Access Control, and full audit logging.

## Team Members
- Member 1 (ID: 52215125139) — Development
- Member 2 (ID: 52215125126) — Security Testing
- Member 3 (ID: 52215125111) — Mitigation
- Member 4 (ID: 52215125714) — GitHub / CI / SCA

## Security Features
- CSRF protection on all forms
- BCrypt password hashing
- RBAC (Admin / Normal User)
- Input validation with whitelisting and regex
- IDOR prevention on all object access
- Session timeout (30 minutes)
- Brute force protection (django-axes, 5 attempts)
- File upload validation (MIME + extension + UUID rename)
- Custom error pages (no stack traces)
- Full audit logging (login, CRUD, admin actions)
- Output encoding (Django auto-escape)
- Secrets via .env (never committed)

## Installation
1. Clone the repo: `git clone https://github.com/yourteam/secure-taskapp`
2. Create venv: `python3 -m venv venv && source venv/bin/activate`
3. Install deps: `pip install -r requirements.txt`
4. Copy env: `cp .env.example .env` then fill in SECRET_KEY
5. Migrate: `python manage.py migrate`
6. Create admin: `python manage.py createsuperuser`
7. Run: `python manage.py runserver`
8. Visit: `http://127.0.0.1:8000`

## Dependencies
See requirements.txt

## Framework
Django 4.x (Python)
