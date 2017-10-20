import docker.errors
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse
import os
import requests
from ..scraper.query import query_single_paper
from .processor import process_render
from .renderer import render_paper, create_client


class DownloadError(Exception):
    """Error downloading a paper."""


class RenderError(Exception):
    pass


class PaperIsNotRenderableError(RenderError):
    """Paper cannot be rendered."""


class RenderAlreadyStartedError(RenderError):
    """Render started when render has already been started."""


class RenderWrongStateError(RenderError):
    """The state of a render is being updated when it has not been started."""


def guess_extension_from_headers(h):
    """
    Given headers from an ArXiV e-print response, try and guess what the file
    extension should be.

    Based on: https://arxiv.org/help/mimetypes
    """
    if h.get('content-type') == 'application/pdf':
        return '.pdf'
    if h.get('content-encoding') == 'x-gzip' and h.get('content-type') == 'application/postscript':
        return '.ps.gz'
    if h.get('content-encoding') == 'x-gzip' and h.get('content-type') == 'application/x-eprint-tar':
        return '.tar.gz'
    # content-encoding is x-gzip but this appears to normally be a lie - it's
    # just plain text
    if h.get('content-type') == 'application/x-eprint':
        return '.tex'
    if h.get('content-encoding') == 'x-gzip' and h.get('content-type') == 'application/x-dvi':
        return '.dvi.gz'
    return None


class PaperQuerySet(models.QuerySet):
    def _with_has_successful_render_annotation(self):
        renders = Render.objects.filter(paper=models.OuterRef('pk'),
                                        state=Render.STATE_SUCCESS)
        return self.annotate(has_successful_render=models.Exists(renders))

    def has_successful_render(self):
        qs = self._with_has_successful_render_annotation()
        return qs.filter(has_successful_render=True)

    def has_no_successful_render(self):
        qs = self._with_has_successful_render_annotation()
        return qs.filter(has_successful_render=False)

    def downloaded(self):
        return self.filter(source_file__isnull=False)

    def not_downloaded(self):
        return self.filter(source_file__isnull=True)

    def update_or_create_from_api(self, result):
        return self.update_or_create(arxiv_id=result['arxiv_id'],
                                     defaults=result)

    def update_or_create_from_arxiv_id(self, arxiv_id):
        """
        Query the Arxiv API and create a Paper from it.

        Raises:
            `arxiv_vanity.scraper.query.PaperNotFoundError`: If paper does not exist on arxiv.
        """
        return self.update_or_create_from_api(query_single_paper(arxiv_id))

    def machine_learning(self):
        """
        Return only machine learning papers.
        """
        return self.filter(categories__overlap=settings.PAPERS_MACHINE_LEARNING_CATEGORIES)


class Paper(models.Model):
    # ArXiV fields
    arxiv_id = models.CharField(max_length=50, unique=True)
    title = models.TextField()
    published = models.DateTimeField()
    updated = models.DateTimeField()
    summary = models.TextField()
    authors = JSONField()
    arxiv_url = models.URLField()
    pdf_url = models.URLField()
    primary_category = models.CharField(max_length=100)
    categories = ArrayField(models.CharField(max_length=100))
    comment = models.TextField(null=True, blank=True)
    doi = models.CharField(null=True, blank=True, max_length=100)
    journal_ref = models.TextField(null=True, blank=True, max_length=100)

    # ASS fields
    source_file = models.FileField(upload_to='paper-sources/', null=True, blank=True)

    objects = PaperQuerySet.as_manager()

    class Meta:
        get_latest_by = 'updated'
        ordering = ['-updated']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('paper_detail', args=(self.arxiv_id,))

    def get_source_url(self):
        # This URL is normally a tarball, but sometimes something else.
        # ArXiV provides a /src/ URL which always serves up a tarball,
        # but if we used this, we'd have to untar the file to figure out
        # whether it's renderable or not. By using the /e-print/ endpoint
        # we can figure out straight away whether we should bother rendering
        # it or not.
        # https://arxiv.org/help/mimetypes has more info
        return 'https://arxiv.org/e-print/' + self.arxiv_id

    def get_https_arxiv_url(self):
        url = self.arxiv_url
        if url.startswith('http://arxiv.org'):
            url = 'https' + url.lstrip('http')
        return url

    def get_https_pdf_url(self):
        url = self.pdf_url
        if url.startswith('http://arxiv.org'):
            url = 'https' + url.lstrip('http')
        return url

    def download(self):
        """
        Download the LaTeX source of this paper and save to storage. It will
        save the model.
        """
        # Delete an existing file if it exists so we don't clutter up storage
        # with dupes. This might mean we lose a file the download fails,
        # but we can just download it again.
        if self.source_file.name:
            self.source_file.delete()

        res = requests.get(self.get_source_url())
        res.raise_for_status()
        extension = guess_extension_from_headers(res.headers)
        if not extension:
            raise DownloadError("Could not determine file extension from "
                                "headers: Content-Type: {}; "
                                "Content-Encoding: {}".format(
                                    res.headers.get('content-type'),
                                    res.headers.get('content-encoding')))
        content = ContentFile(res.content)
        self.source_file.save(self.arxiv_id + extension, content)

    def is_renderable(self):
        """
        Returns whether it is possible to render this paper.
        """
        return self.source_file.name is not None and self.source_file.name.endswith('.tar.gz')

    def render(self):
        """
        Make a new render of this paper. Will download the source file and save
        itself if it hasn't already.
        """
        if not self.source_file.name:
            self.download()
        if not self.is_renderable():
            raise PaperIsNotRenderableError("This paper is not renderable.")
        render = Render.objects.create(paper=self)
        render.run()


class RenderQuerySet(models.QuerySet):
    def running(self):
        return self.filter(state=Render.STATE_RUNNING)

    def succeeded(self):
        return self.filter(state=Render.STATE_SUCCESS)

    def failed(self):
        return self.filter(state=Render.STATE_FAILURE)

    def update_state(self):
        """
        Update the state of renders that have a container.
        """
        for render in self.exclude(state=Render.STATE_UNSTARTED).filter(container_is_removed=False):
            try:
                render.update_state()
            except docker.errors.NotFound:
                # TODO: logging
                print(f"Could not update render {render.id}: Container ID {render.container_id} does not exist")
        return self


class Render(models.Model):
    STATE_UNSTARTED = 'unstarted'
    STATE_RUNNING = 'running'
    STATE_SUCCESS = 'success'
    STATE_FAILURE = 'failure'

    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name='renders')
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=20, default=STATE_UNSTARTED, choices=(
        (STATE_UNSTARTED, 'Unstarted'),
        (STATE_RUNNING, 'Running'),
        (STATE_SUCCESS, 'Success'),
        (STATE_FAILURE, 'Failure'),
    ))
    container_id = models.CharField(max_length=64, null=True, blank=True)
    container_inspect = JSONField(null=True, blank=True)
    container_logs = models.TextField(null=True, blank=True)
    container_is_removed = models.BooleanField(default=False)

    objects = RenderQuerySet.as_manager()

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.paper.title

    def save(self, *args, **kwargs):
        super(Render, self).save(*args, **kwargs)

    def get_output_path(self):
        """
        Path to the directory that this render is in.
        """
        return os.path.join('render-output', str(self.id))

    def get_html_path(self):
        """
        Path to the HTML file of this render.
        """
        return os.path.join(self.get_output_path(), "index.html")

    def get_output_url(self):
        """
        Returns the URL to the output path.
        """
        return settings.MEDIA_URL + self.get_output_path()

    def short_container_id(self):
        if self.container_id:
            return self.container_id[:12]

    def get_webhook_url(self):
        """
        Get the webhook to call when the Engrafo job ends to update render
        state.
        """
        path = reverse('render_update_state', args=(self.id,))
        return settings.ENGRAFO_WEBHOOK_URL_PREFIX + path

    def run(self):
        """
        Start running this render.
        """
        if self.state != Render.STATE_UNSTARTED:
            raise RenderAlreadyStartedError(f"Render {self.id} has already been started")
        self.container_id = render_paper(
            self.paper.source_file.name,
            self.get_output_path(),
            webhook_url=self.get_webhook_url()
        )
        self.state = Render.STATE_RUNNING
        self.save()

    def update_state(self, exit_code=None):
        """
        Update state of this render from the container.

        This is used for two purposes:

        1. Called by the webhook to update the state. In this case, exit_code
            is passed through instead of using the containers exit code
            because the container is still running (it's sending the webhook!).

        2. Called by the update_render_state cron job. In this case, it'll
            sync all of the details about the containers that exist, and remove
            any containers that have stopped. This sweeps up containers
            that have reported their state in (1).
        """
        if self.state == Render.STATE_UNSTARTED:
            raise RenderWrongStateError(f"Render {self.id} has not been started")
        client = create_client()

        try:
            container = client.containers.get(self.container_id)
            self.container_inspect = container.attrs
            self.container_logs = container.logs()
        except docker.errors.NotFound:
            # Container has been removed for some reason, so mark it as
            # removed so we don't try to update its state again
            self.container_is_removed = True
            self.save()
            return

        if exit_code is None and container.status == 'exited':
            exit_code = container.attrs['State']['ExitCode']

        if exit_code is not None:
            # Safer to convert int to str than other way round
            if str(exit_code) == '0':
                self.state = Render.STATE_SUCCESS
            else:
                self.state = Render.STATE_FAILURE

        if container.status == 'exited':
            try:
                container.remove()
            except docker.errors.NotFound:
                # Somebody got in there before us. Oh well.
                pass
            self.container_is_removed = True

        self.save()

    def get_processed_render(self):
        """
        Do final processing on this render and returns it as a dictionary of
        {"body", "script", "styles"}.
        """
        context = {
            'render': self,
            'paper': self.paper,
        }
        with default_storage.open(self.get_html_path()) as fh:
            return process_render(fh, self.get_output_url(), context=context)
