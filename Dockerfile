FROM python:3.6
RUN apt-get update -qq && apt-get install -qy netcat
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/
RUN SECRET_KEY=unset python manage.py collectstatic --no-input
ENV WEB_CONCURRENCY 3
ENV PORT 8000
CMD gunicorn arxiv_vanity.wsgi -k gevent --worker-connections 100 --bind 0.0.0.0:8000 --config gunicorn_config.py
