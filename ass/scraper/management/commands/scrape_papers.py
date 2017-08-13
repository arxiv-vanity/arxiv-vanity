from django.core.management.base import BaseCommand, CommandError
from ...query import scrape_papers

class Command(BaseCommand):
    help = 'Scrape latest papers from Arxiv'

    def handle(self, *args, **options):
        scrape_papers()
