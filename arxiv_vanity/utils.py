from functools import wraps
import traceback
import os
from raven.contrib.django.raven_compat.models import client


def log_exception():
    traceback.print_exc()
    if os.environ.get('SENTRY_DSN'):
        client.captureException()


def catch_exceptions(f):
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception:
            log_exception()
    return inner
