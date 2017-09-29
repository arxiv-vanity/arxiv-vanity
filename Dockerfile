FROM python:3.6
RUN apt-get update -qq && apt-get install -qy netcat
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/
RUN SECRET_KEY=unset python manage.py collectstatic --no-input
ENV PORT 8000
CMD gunicorn arxiv_vanity.wsgi -b 0.0.0.0:$PORT --log-file - --access-logfile - -k eventlet --workers 4 --worker-connections 5
