# MMORPG Board

Django web application for an MMORPG community board. Users can register, create ads, respond to ads and receive email notifications.

## Tech Stack

- Python
- Django
- Django ORM
- Django Allauth
- PostgreSQL
- Redis
- Celery
- django-celery-beat
- django-filter
- django-ckeditor
- HTML/CSS

## Features

- User registration and authentication
- Custom user profile with avatar and personal data
- Ads CRUD
- Categories for ads
- Responses to ads
- Accept/reject response flow
- Email notifications
- Background tasks with Celery and Redis
- Django admin customization

## Run Locally

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set your local values:

```bash
cp .env.example .env
```

Apply migrations:

```bash
python manage.py migrate
```

Run the development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## Environment Variables

The project reads secrets and local settings from `.env`.

Important variables:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

## What This Project Shows

- Django project structure
- Models, views, forms and templates
- User authentication and permissions
- Working with PostgreSQL
- Background jobs with Celery/Redis
- Email notifications
- Preparing a Django project for GitHub
