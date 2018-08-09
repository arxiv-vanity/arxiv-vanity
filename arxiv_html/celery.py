import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arxiv_html.settings')

app = Celery('arxiv_html')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
