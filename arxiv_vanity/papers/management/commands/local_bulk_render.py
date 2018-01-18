import sys
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from gevent.pool import Pool
from ....utils import catch_exceptions
from ...renderer import render_paper


class BulkRenderer(object):
    def __init__(self, concurrency, output_bucket):
        self.concurrency = concurrency
        self.output_bucket = output_bucket

    def run(self, arxiv_ids):
        print(f"Rendering {len(arxiv_ids)} arXiv IDs...")
        pool = Pool(self.concurrency)
        done = 0
        for result in pool.imap_unordered(self.render, arxiv_ids):
            if not result:
                continue
            arxiv_id, exit_code = result
            if exit_code == 0:
                status = "success"
            else:
                status = "failure"
            done += 1
            print(f"{arxiv_id}: {status} ({done} of {len(arxiv_ids)})", file=sys.stderr)

    @catch_exceptions
    def render(self, arxiv_id):
        output_path = arxiv_id.replace('/', '')
        container = render_paper(
            source=f'source-files/{output_path}.gz',
            output_path=output_path,
            output_bucket=self.output_bucket,
            extra_run_kwargs={'remove': True}
        )
        exit_code = container.wait(timeout=30 * 60)
        return arxiv_id, exit_code


class Command(BaseCommand):
    help = """Render a set of Arxiv IDs to an S3 bucket, keyed by Arxiv ID.
    Arxiv IDs are read from a file in the bucket, one per line.

    Designed to work on a local Docker instance with a lot of RAM.
    See "bulk_render" for the Hyper.sh version.
    """

    def add_arguments(self, parser):
        parser.add_argument('output_bucket', nargs=1, help="S3 bucket to write result to.")
        parser.add_argument('id_filename', nargs=1, help="Path to file containing Arxiv IDs.")
        parser.add_argument('--concurrency', type=int, default=10, help='number of parallel instances to run (default: 10)')

    def handle(self, *args, **options):
        if not settings.MEDIA_USE_S3:
            raise CommandError("MEDIA_USE_S3 is False. This command is designed to work with S3.")
        if settings.ENGRAFO_USE_HYPER_SH:
            raise CommandError("ENGRAFO_USE_HYPER_SH is True. This command is designed to work with a local Docker instance.")
        renderer = BulkRenderer(
            concurrency=options['concurrency'],
            output_bucket=options['output_bucket'][0]
        )

        arxiv_ids = []
        with open(options['id_filename'][0]) as f:
            for line in f:
                line = line.strip()
                if line:
                    arxiv_ids.append(line)

        renderer.run(arxiv_ids)
