from django.core.management.base import BaseCommand, CommandError
from ...models import Render


class Command(BaseCommand):
    help = 'Marks all renders as expired so they will be rerendered'

    def handle(self, *args, **options):
        count = Render.objects.all().force_expire()
        print(f"Marked {count} renders as expired")
