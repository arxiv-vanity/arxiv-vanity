from django.core.management.base import BaseCommand, CommandError
from ...models import Render


class Command(BaseCommand):
    help = 'Deletes output of all expired renders'

    def handle(self, *args, **options):
        for render in Render.objects.expired().iterator():
            try:
                render.delete_output()
            except FileNotFoundError:
                print(f"❌  Render {render.id} already deleted")
            else:
                print(f"✅  Render {render.id} deleted")

