from django.core.management.base import BaseCommand, CommandError
from ...bulk_sources import update_bulk_sources


class Command(BaseCommand):
    help = "Download latest bulk sources from arXiv"

    def handle(self, *args, **options):
        update_bulk_sources()
