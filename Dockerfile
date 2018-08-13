FROM python:3.6.5
RUN apt-get update -qq && apt-get install -qy netcat
RUN pip install -U pip pipenv
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY Pipfile Pipfile.lock /code/
RUN pipenv install --system --deploy
COPY . /code/
RUN SECRET_KEY=unset python manage.py collectstatic --no-input
ENV PORT 8000
CMD gunicorn arxiv_html.wsgi --bind 0.0.0.0:$PORT
