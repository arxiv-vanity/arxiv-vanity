from functools import wraps
import traceback
from raven.contrib.django.raven_compat.models import client


def catch_exceptions(f):
    @wraps(f)
    def inner(*args, **kwargs):
        try:
           return f(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            client.captureException()
    return inner
