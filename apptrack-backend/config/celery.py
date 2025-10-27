"""
Celery configuration for apptrack project.
"""

import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('apptrack')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'send-reminders': {
        'task': 'apps.applications.tasks.send_scheduled_reminders',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    },
    'cleanup-old-data': {
        'task': 'apps.core.tasks.cleanup_old_data',
        'schedule': crontab(hour=3, minute=0),  # Run daily at 3 AM
    },
}

# Configure timezone
app.conf.timezone = settings.TIME_ZONE

# Task configuration
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 100
app.conf.task_time_limit = 30 * 60  # 30 minutes

# Task routing
app.conf.task_routes = {
    'apps.applications.tasks.*': {'queue': 'applications'},
    'apps.core.tasks.*': {'queue': 'core'},
}

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
