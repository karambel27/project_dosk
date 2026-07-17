# MMORPG Board

Django-сайт сообщества MMORPG: пользователи регистрируются, подтверждают email, публикуют объявления по категориям и отправляют отклики. Автор объявления может принять или отклонить отклик, а участники получают фоновые email-уведомления и еженедельный digest.

Проект использует server-rendered templates, session authentication и CSRF. JWT здесь не нужен: браузерное приложение не имеет отдельного SPA/mobile API, а защищённые cookie и object-level ownership checks соответствуют его архитектуре.

## Возможности

- регистрация и обязательная email-верификация через django-allauth;
- пользовательский профиль и аватар;
- создание, редактирование, публикация и удаление своих объявлений;
- категории, поиск и пагинация;
- черновики, доступные только владельцу;
- один отклик пользователя на объявление;
- запрет отклика на собственное объявление;
- POST-only принятие/отклонение с CSRF-защитой;
- Celery-задачи с retry для email-уведомлений;
- еженедельная рассылка через Celery Beat;
- eager loading и агрегаты без N+1;
- серверная очистка пользовательского HTML;
- production-профиль PostgreSQL/Redis/Gunicorn/WhiteNoise;
- тесты permissions, ownership, ORM и фоновых уведомлений.

## Стек

- Python 3.12+
- Django 6, django-allauth, django-filter
- PostgreSQL / SQLite
- Celery, Redis
- Bleach, Pillow
- Gunicorn, WhiteNoise
- Ruff, Django TestCase
- Docker, Docker Compose, GitHub Actions

## Локальный запуск

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

Примените миграции и запустите сервер:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Откройте `http://127.0.0.1:8000/`. Категории можно создать через Django Admin.

Локально используется PostgreSQL, email выводятся в консоль, а Celery-задачи выполняются в eager-режиме. 

## Полный запуск в Docker

```bash
docker compose up --build
```

Compose поднимает пять сервисов:

- `web` — Django + Gunicorn;
- `db` — PostgreSQL 16;
- `redis` — broker/result backend;
- `worker` — Celery worker;
- `beat` — еженедельный планировщик.

После healthchecks приложение доступно на `http://127.0.0.1:8000/`. Значения паролей в Compose предназначены только для локальной разработки; при развёртывании секреты должны поступать из настроек платформы или secret storage.

## Настройки

| Переменная | Назначение |
| --- | --- |
| `DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS` | базовые Django settings |
| `CSRF_TRUSTED_ORIGINS` | доверенные HTTPS origins |
| `DB_ENGINE` | `sqlite` или `postgresql` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | доступ к PostgreSQL |
| `DB_HOST`, `DB_PORT` | адрес PostgreSQL |
| `EMAIL_BACKEND` | console backend локально, SMTP в production |
| `EMAIL_HOST*`, `DEFAULT_FROM_EMAIL` | SMTP settings |
| `CELERY_BROKER_URL` | Redis broker |
| `CELERY_RESULT_BACKEND` | Redis result backend |
| `CELERY_TASK_ALWAYS_EAGER` | синхронный dev/test режим задач |

При `DEBUG=false` приложение требует отдельный `SECRET_KEY`, разрешённые hosts и PostgreSQL. Production-профиль включает secure cookies, HSTS, HTTPS redirect и WhiteNoise; TLS обычно завершается на reverse proxy.

## Безопасность workflow

- Изменение статуса отклика принимает только `POST` с CSRF token.
- Статус может изменить только автор объявления или superuser.
- Принятый/отклонённый отклик нельзя повторно перевести другим действием.
- Черновик скрыт от всех, кроме автора и superuser.
- Allauth использует подписанные ссылки с ограниченным сроком вместо самодельного короткого кода.
- Поле объявления очищается через Bleach перед сохранением; неподдерживаемый CKEditor 4 удалён.
- Email ставятся в очередь после успешного commit транзакции.

## Проверки

```bash
ruff check .
ruff format --check .
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py check --deploy
```

Тесты сравнивают количество SQL-запросов при росте списка объявлений, проверяют ownership, запрет self-response, POST-only actions, очистку HTML, постановку Celery-задач и адресатов email.

## Структура

```text
.
├── ads/                  # объявления, отклики, tasks/signals, templates
├── users/                # custom user и профиль
├── config/               # settings, URLs, Celery, ASGI/WSGI
├── templates/            # base и allauth templates
├── static/               # CSS и интерфейсные изображения
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── requirements*.txt
```
