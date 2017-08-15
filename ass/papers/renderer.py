import docker
from django.conf import settings
import os


def render_paper(source, output_path):
    try:
        os.makedirs(output_path)
    except FileExistsError:
        pass
    client = docker.from_env()
    container = client.containers.run(
        settings.ENGRAFO_IMAGE,
        [
            "engrafo",
            "-o", os.path.join('/mnt', output_path),
            os.path.join('/mnt', source),
        ],
        volumes={os.environ['HOST_PWD']: {'bind': '/mnt', 'mode': 'rw'}},
        detach=True,
    )
    return container.id
