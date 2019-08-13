from django.core.management.base import BaseCommand, CommandError
from ...renderer import pull_image


class Command(BaseCommand):
    help = "Pull the configured Engrafo image"

    def handle(self, *args, **options):
        image = pull_image()
        print(f"Pulled {image.attrs['Id']}")
