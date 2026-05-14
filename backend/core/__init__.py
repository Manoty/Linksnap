# core/__init__.py
# Ensures the Celery app is loaded when Django starts.
# Required for @shared_task decorators to bind correctly.

from core.celery import app as celery_app

__all__ = ('celery_app',)