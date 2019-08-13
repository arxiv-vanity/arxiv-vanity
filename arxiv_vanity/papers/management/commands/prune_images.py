from django.core.management.base import BaseCommand, CommandError
from ...renderer import prune_images


class Command(BaseCommand):
    help = "Prune unused images from Docker server"

    def handle(self, *args, **options):
        prune_images()
