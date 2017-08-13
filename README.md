# ASS

## Running in development

Install Docker for Mac or Windows.

Do the initial database migration and set up a user:

    $ docker-compose run web ./manage.py migrate
    $ docker-compose run web ./manage.py createsuperuser

Then to run the app:

    $ docker-compose up --build

Your app is now available at [http://localhost:8000](http://localhost:8000). The admin interface is at [http://localhost:8000/admin/](http://localhost:8000/admin/).

## Running tests

    $ script/test
