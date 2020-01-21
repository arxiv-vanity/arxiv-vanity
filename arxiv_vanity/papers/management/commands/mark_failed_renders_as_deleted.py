from django.core.management.base import BaseCommand, CommandError
from ...models import Render


class Command(BaseCommand):
    help = "Marks all failed renders as deleted so they will be rerendered"

    def handle(self, *args, **options):
        qs = (
            Render.objects.defer("container_inspect", "container_logs")
            .failed()
            .not_deleted()
        )
        qs.mark_as_deleted()
        print(f"Done")
