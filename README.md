# Arxiv Vanity

## Running in development

Install Docker for Mac or Windows.

Do the initial database migration and set up a user:

    $ script/manage migrate
    $ script/manage createsuperuser

Then to run the app:

    $ docker-compose up --build

Your app is now available at [http://localhost:8000](http://localhost:8000). The admin interface is at [http://localhost:8000/admin/](http://localhost:8000/admin/).

You can scrape some papers from Arxiv by running:

    $ script/manage scrape_papers

It'll probably fetch quite a lot, so hit `ctrl-C` when you've got enough.

## Running tests

    $ script/test
