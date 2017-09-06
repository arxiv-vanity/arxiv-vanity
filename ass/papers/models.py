import datetime
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.urls import reverse
import os
import requests
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
    def succeeded(self):
        return self.filter(state=Render.STATE_SUCCESS)

    def failed(self):
        return self.filter(state=Render.STATE_FAILURE)

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

    def run(self):
        """
        Start running this render.
        """
        if self.state != Render.STATE_UNSTARTED:
            raise RenderAlreadyStartedError("Render {} has already been started".format(self.id))
        self.container_id = render_paper(
            self.paper.source_file.name,
            self.get_output_path()
        )
        self.state = Render.STATE_RUNNING
        self.save()

    def update_state(self):
        """
        Update state of this render from the container.
        """
        if self.state == Render.STATE_UNSTARTED:
            raise RenderWrongStateError("Render {} has not been started".format(self.id))
        if self.state in (Render.STATE_SUCCESS, Render.STATE_FAILURE):
            raise RenderWrongStateError("Render {} has already had state set".format(self.id))
        client = create_client()
        container = client.containers.get(self.container_id)
        self.container_inspect = container.attrs
        if container.status == 'exited':
            self.container_logs = container.logs()
            if container.attrs['State']['ExitCode'] == 0:
                self.state = Render.STATE_SUCCESS
            else:
                self.state = Render.STATE_FAILURE
            container.remove()
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
