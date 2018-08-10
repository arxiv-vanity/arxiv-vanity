from ..celery import app
from .engrafo import run_engrafo


@app.task(bind=True)
def run_engrafo_task(self, *args, **kwargs):
    exit_code, logs = run_engrafo(*args, **kwargs)
    if exit_code != 0:
        return self.update_state(state="FAILURE", meta={"logs": logs})
    return {"logs": logs}
