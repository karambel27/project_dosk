import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')

app = Celery('ads')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
app.conf.update(
    CELERY_TIMEZONE= 'Asia/Vladivostok',
    CELERYD_POOL = 'solo',
)

app.conf.beat_schedule = {
    'ads_task': {
        'task': 'ads.tasks.send_weekly_digest',
        'schedule': crontab(hour=10, minute=0, day_of_week=1),
        'args': (),
    }
}


