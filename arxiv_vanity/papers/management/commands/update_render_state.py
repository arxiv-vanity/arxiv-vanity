from django.core.management.base import BaseCommand, CommandError
from ...models import Render


class Command(BaseCommand):
    help = 'Sync the state of renders in the database with what is on Docker'

    def handle(self, *args, **options):
        Render.objects.update_state()
        Render.objects.update_is_expired()
