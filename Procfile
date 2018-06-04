web: gunicorn arxiv_vanity.wsgi -k gevent --worker-connections 100 --bind 0.0.0.0:$PORT --config gunicorn_config.py --max-requests 10000 --max-requests-jitter 1000 --access-logfile -
