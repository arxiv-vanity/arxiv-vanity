from django.core.management.base import BaseCommand, CommandError
from ...models import Render


class Command(BaseCommand):
    help = "Marks all renders as expired so they will be rerendered"

    def handle(self, *args, **options):
        qs = Render.objects.defer("container_inspect", "container_logs").not_expired()
        qs.force_expire()
        print(f"Done")
