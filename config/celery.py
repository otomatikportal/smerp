import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
app = Celery('smerp')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# celery.py
app.conf.beat_schedule = {
    'fetch-exchange-rates-daily': {
        'task': 'finance.tasks.fetch_daily_exchange_rates',
        'schedule': crontab(hour=5, minute=0),  # Every day at 5:00
    },
}
