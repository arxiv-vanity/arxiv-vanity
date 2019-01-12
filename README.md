# Arxiv Vanity

[Arxiv Vanity](https://www.arxiv-vanity.com) renders papers from [Arxiv](https://arxiv.org) as responsive web pages so you don't have to squint at a PDF.

It turns this sort of thing:

<img src="docs/screenshot-pdf.png" width="600">

Into this:

<img src="docs/screenshot-screens.png">

This is the web interface for viewing papers. The actual LaTeX to HTML conversion (the interesting bit) is done by [Engrafo](https://github.com/arxiv-vanity/engrafo).

## Running in development

Install Docker for Mac or Windows.

Do the initial database migration and set up a user:

    $ script/manage migrate
    $ script/manage createsuperuser

Then to run the app:

    $ docker-compose up --build

Your app is now available at [http://localhost:8000](http://localhost:8000). The admin interface is at [http://localhost:8000/admin/](http://localhost:8000/admin/).

You can scrape the latest papers from Arxiv by running:

    $ script/manage scrape_papers

It'll probably fetch quite a lot, so hit `ctrl-C` when you've got enough.

## Running tests

    $ script/test

## Sponsors

Thanks to our generous sponsors for supporting the development of Arxiv Vanity! [Sponsor us to get your logo here.](https://www.patreon.com/arxivvanity)

[<img src="arxiv_vanity/static/sponsor-yld.png" alt="YLD" width="250" />](https://www.yld.io/)
