FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN DEBUG=false \
    SECRET_KEY=build-only-secret-not-used-at-runtime \
    ALLOWED_HOSTS=localhost \
    DB_ENGINE=postgresql \
    DB_NAME=build \
    DB_USER=build \
    DB_PASSWORD=build \
    DB_HOST=localhost \
    SECURE_SSL_REDIRECT=false \
    SECURE_HSTS_SECONDS=0 \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 60"]
