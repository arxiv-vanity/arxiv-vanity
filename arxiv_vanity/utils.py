from django.conf import settings
from functools import wraps
import traceback
import os
from sentry_sdk import capture_exception


def log_exception():
    """
    Log an exception that has been raised to the console and Sentry.
    Must be called within an `except ...:` statement.
    """
    traceback.print_exc()
    if settings.SENTRY_DSN:
        capture_exception()


def catch_exceptions(f):
    """
    A decorator that makes a function never raise an exception.
    If it does, it will log it to the console and Sentry.
    """
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            log_exception()
    return inner
