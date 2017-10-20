import time
import docker.errors
from django.core.management.base import BaseCommand, CommandError
from ...models import Paper
from .update_render_state import update_render_state


class Command(BaseCommand):
    help = 'Rerender all papers'

    def handle(self, *args, **options):
        print("Rendering papers", end='')
        for paper in Paper.objects.all():
            paper.render()
            print('.', end='', flush=True)

        print()
