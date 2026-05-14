# Celery application entry point.
# Imported by core/__init__.py so tasks are discoverable from the start.

import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('qejani')

# Pull all CELERY_* settings from Django settings automatically
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks.py in every INSTALLED_APP
app.autodiscover_tasks()