from ..celery import app
from .engrafo import run_engrafo


@app.task(bind=True)
def run_engrafo_task(self, *args, **kwargs):
    return run_engrafo(*args, **kwargs)
