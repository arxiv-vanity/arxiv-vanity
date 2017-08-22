import docker.errors
from django.core.management.base import BaseCommand, CommandError
from ...models import Render


def update_render_state():
    for render in Render.objects.filter(state=Render.STATE_RUNNING):
        try:
            render.update_state()
        except docker.errors.NotFound:
            print("Could not update render {}: Container ID {} does not exist".format(render.id, render.container_id))


class Command(BaseCommand):
    help = 'Sync the state of renders in the database with what is on Docker'

    def handle(self, *args, **options):
        update_render_state()
