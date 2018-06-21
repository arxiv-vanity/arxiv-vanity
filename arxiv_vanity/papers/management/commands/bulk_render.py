import json
import socket
import sys
import time
from django.core.management.base import BaseCommand, CommandError
from gevent.pool import Pool
from requests.exceptions import HTTPError, ConnectionError
from storages.backends.s3boto3 import S3Boto3Storage
from ....utils import catch_exceptions
from ...models import SourceFile
from ...renderer import render_paper


def keep_on_trying(f, *args, **kwargs):
    """
    Deal with Hyper.sh's menangerie of error messages.
    """
    n = 0
    while True:
        try:
            return f(*args, **kwargs)
        except HTTPError as e:
            # 429: Too Many Requests for url
            if e.response.status_code == 429 or e.response.status_code >= 500:
                time.sleep(10)
            else:
                raise
        except ConnectionError:
            pass
        n += 1
        if n > 10:
            break


class BulkRenderer(object):
    def __init__(self, concurrency, output_bucket):
        self.concurrency = concurrency
        self.output_bucket = output_bucket

    def run(self, id_filename):
        s3 = S3Boto3Storage().connection
        obj = s3.Object(self.output_bucket, id_filename)
        arxiv_id_str = obj.get()['Body'].read().decode('utf-8')
        arxiv_ids = [s.strip() for s in arxiv_id_str.split() if s.strip()]

        # We can't access database inside our gevent pool because of max
        # connections, so first figure out which IDs we actually want to
        # render.
        arxiv_ids, source_paths = self.filter_unrenderable_ids(arxiv_ids)

        # Stagger the starting of jobs a bit so we don't break Hyper.sh
        def slow_arxiv_ids():
            for arxiv_id in arxiv_ids:
                yield arxiv_id
                time.sleep(0.1)

        pool = Pool(self.concurrency)
        manifest = pool.imap_unordered(self.render, slow_arxiv_ids(), source_paths)
        # Failed renders are None
        manifest = (obj for obj in manifest if obj)
        # Read the iterator, starting the actual processing
        manifest = list(manifest)
        self.write_manifest(manifest)

    def filter_unrenderable_ids(self, arxiv_ids):
        ids_to_render = []
        source_paths = []
        for arxiv_id in arxiv_ids:
            try:
                source_file = SourceFile.objects.get(arxiv_id=arxiv_id)
            except SourceFile.DoesNotExist:
                print(f"{arxiv_id} has no source file, skipping")
                continue

            if source_file.is_pdf():
                print(f"{arxiv_id} source is a PDF, skipping")
                continue

            ids_to_render.append(arxiv_id)
            source_paths.append(source_file.file.name)
        return arxiv_ids, source_paths

    @catch_exceptions
    def render(self, arxiv_id, source_path):
        print(f"Rendering {arxiv_id}", file=sys.stderr)
        output_path = arxiv_id.replace('/', '')
        container = keep_on_trying(
            render_paper,
            source=source_path,
            output_path=output_path,
            output_bucket=self.output_bucket,
        )
        try:
            exit_code = keep_on_trying(container.wait)
        finally:
            try:
                container.kill()
            except Exception:
                pass
            try:
                container.remove()
            except Exception:
                pass

        if exit_code == 0:
            return {
                'arxiv_id': arxiv_id,
                'output_path': output_path
            }

    def write_manifest(self, manifest):
        s3 = S3Boto3Storage().connection
        manifest_json = json.dumps(manifest, indent=2)
        s3.Object(self.output_bucket, 'manifest.json').put(Body=manifest_json)


class Command(BaseCommand):
    help = 'Render a set of Arxiv IDs to an S3 bucket, keyed by Arxiv ID. Arxiv IDs are read from a file in the bucket, one per line.'

    def add_arguments(self, parser):
        parser.add_argument('output_bucket', nargs=1, help="S3 bucket to write result to.")
        parser.add_argument('id_filename', nargs=1, help="File in S3 containing Arxiv IDs.")

    def handle(self, *args, **options):
        renderer = BulkRenderer(
            concurrency=500,
            output_bucket=options['output_bucket'][0]
        )
        renderer.run(options['id_filename'][0])
