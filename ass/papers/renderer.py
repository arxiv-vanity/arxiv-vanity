import docker
from django.conf import settings
import os


def render_paper(source, output_path):
    try:
        os.makedirs(output_path)
    except FileExistsError:
        pass
    client = docker.from_env()

    # Production
    if settings.MEDIA_USE_S3:
        source = "s3://{}/{}".format(settings.AWS_STORAGE_BUCKET_NAME,
                                     source)
        output_path = "s3://{}/{}".format(settings.AWS_STORAGE_BUCKET_NAME,
                                          output_path)
        volumes = {}
        environment = {
            'AWS_ACCESS_KEY_ID': settings.AWS_ACCESS_KEY_ID,
            'AWS_SECRET_ACCESS_KEY': settings.AWS_SECRET_ACCESS_KEY,
            'AWS_S3_REGION_NAME': settings.AWS_S3_REGION_NAME,
        }
    # Development
    else:
        # HACK(bfirsh): MEDIA_ROOT is an absolute path to something on
        # the host machine. We need to make this relative to a mount inside the
        # Docker container.
        docker_media_root = os.path.join(
            '/mnt',
            os.path.basename(settings.MEDIA_ROOT)
        )
        source = os.path.join(docker_media_root, source)
        output_path = os.path.join(docker_media_root, output_path)
        # HOST_PWD is set in docker-compose.yml
        volumes = {os.environ['HOST_PWD']: {'bind': '/mnt', 'mode': 'rw'}}
        environment = {}

    container = client.containers.run(
        settings.ENGRAFO_IMAGE,
        ["engrafo", "-o", output_path, source],
        volumes=volumes,
        environment=environment,
        detach=True,
    )
    return container.id
