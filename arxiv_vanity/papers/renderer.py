import datetime
import os
import shlex
from docker import DockerClient
from docker.tls import TLSConfig
import hyper_sh
from django.conf import settings
import dateutil.parser
import tempfile
from ..utils import log_exception


def env_to_file(env):
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(os.environ[env].encode('utf-8'))
        return f.name


def create_client():
    """
    Create a client to either a local Docker instance or Hyper.sh.
    """
    kwargs = {
        'base_url': os.environ.get('DOCKER_HOST'),
        # Sometimes Hyper.sh is very slow.
        'timeout': 60 * 10
    }

    if os.environ.get('DOCKER_TLS_VERIFY'):
        kwargs['tls'] = TLSConfig(
            client_cert=(env_to_file('DOCKER_CLIENT_CERT'), env_to_file('DOCKER_CLIENT_KEY')),
            ca_cert=env_to_file('DOCKER_CA_CERT'),
            verify=True
        )

    client = DockerClient(**kwargs)
    if settings.ENGRAFO_USE_HYPER_SH:
        client.api = hyper_sh.Client({
            'clouds': {
                settings.HYPER_ENDPOINT: {
                    'accesskey': settings.HYPER_ACCESS_KEY,
                    'secretkey': settings.HYPER_SECRET_KEY,
                }
            }
        })
        client.api.timeout = timeout
    return client


def make_command(source, output_path, webhook_url):
    command = [
        f"engrafo -o {shlex.quote(output_path)} {shlex.quote(source)}",
        f"EXIT_CODE=$?"
    ]
    if webhook_url:
        # Pass through exit code to webhook because this container hasn't
        # actually exited yet
        command.extend([
            f"echo Calling webhook {shlex.quote(webhook_url)} with payload exit_code=$EXIT_CODE",
            f"curl -D - -X POST -F exit_code=$EXIT_CODE {shlex.quote(webhook_url)}"
        ])

    command.append("exit $EXIT_CODE")
    return command


def render_paper(source, output_path, webhook_url=None, output_bucket=None, extra_run_kwargs=None):
    """
    Render a source directory using Engrafo.
    """
    client = create_client()

    labels = {}
    environment = {}
    volumes = {}
    network = None

    # Production
    if settings.MEDIA_USE_S3:
        if output_bucket is None:
            output_bucket = settings.AWS_STORAGE_BUCKET_NAME
        source = f"s3://{settings.AWS_STORAGE_BUCKET_NAME}/{source}"
        output_path = f"s3://{output_bucket}/{output_path}"
        environment['AWS_ACCESS_KEY_ID'] = settings.AWS_ACCESS_KEY_ID
        environment['AWS_SECRET_ACCESS_KEY'] = settings.AWS_SECRET_ACCESS_KEY
        environment['AWS_S3_REGION_NAME'] = settings.AWS_S3_REGION_NAME
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
        volumes[os.environ['HOST_PWD']] = {'bind': '/mnt', 'mode': 'rw'}

    if settings.ENGRAFO_USE_HYPER_SH:
        labels['sh_hyper_instancetype'] = settings.HYPER_INSTANCE_TYPE

    # If running on the local machine, we need to add the container to the same network
    # as the web app so it can call the callback
    if os.environ.get("DOCKER_HOST") == "unix:///var/run/docker.sock":
        network = 'arxiv-vanity_default'

    if extra_run_kwargs is None:
        extra_run_kwargs = {}
    return client.containers.run(
        settings.ENGRAFO_IMAGE,
        'sh -c ' + shlex.quote('; '.join(make_command(source, output_path, webhook_url))),
        volumes=volumes,
        environment=environment,
        labels=labels,
        network=network,
        detach=True,
        **extra_run_kwargs
    )


def pull_image():
    client = create_client()
    print(f"Pulling {settings.ENGRAFO_IMAGE}...")
    return client.images.pull(settings.ENGRAFO_IMAGE)


def prune_images():
    client = create_client()
    for image in client.images.list(filters={'dangling': True}):
        image_id = image.attrs['Id']
        print(f"Removing {image_id}...")
        try:
            client.images.remove(image_id)
        except docker.errors.APIError as e:
            if e.response.status_code == 409:
                print(f"Image {image_id} in use")
            else:
                raise

def remove_long_running_containers():
    """
    Sometimes either a container will get stuck, or the container can't
    be removed. So, just keep on sweeping up.
    """
    client = create_client()
    for container in client.api.containers(all=True):
        delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(container['Created'])
        if delta > datetime.timedelta(minutes=5):
            print(f"Container {container['Id'][:12]} has been running for >5 mins, force removing")
            try:
                client.api.remove_container(container['Id'], force=True)
            except:
                log_exception()
