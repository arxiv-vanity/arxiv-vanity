from django.core.management.base import BaseCommand, CommandError
from ...models import Render
from ...renderer import remove_long_running_containers


class Command(BaseCommand):
    help = "Sync the state of renders in the database with what is on Docker"

    def handle(self, *args, **options):
        print("Updating state...")
        Render.objects.update_state()
        print("Removing long running containers...")
        remove_long_running_containers()
