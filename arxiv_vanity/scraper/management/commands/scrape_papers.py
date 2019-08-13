from django.core.management.base import BaseCommand, CommandError
from ...scraper import scrape_and_render_papers


class Command(BaseCommand):
    help = "Scrape latest papers from arXiv"

    def handle(self, *args, **options):
        scrape_and_render_papers()
