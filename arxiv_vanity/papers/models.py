import datetime
import docker.errors
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.files.storage import default_storage
from django.urls import reverse
from django.utils import timezone
import os
from ..scraper.query import query_single_paper
from ..storage import storage_delete_path
from ..utils import log_exception
from .downloader import download_source_file
from .processor import process_render
from .renderer import render_paper, create_client


class RenderError(Exception):
    pass


class PaperIsNotRenderableError(RenderError):
    """Paper cannot be rendered."""


class RenderAlreadyStartedError(RenderError):
    """Render started when render has already been started."""


class RenderWrongStateError(RenderError):
    """The state of a render is being updated when it has not been started."""


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

    def _with_has_not_expired_render_annotation(self):
        renders = Render.objects.filter(paper=models.OuterRef('pk'),
                                        is_expired=False)
        return self.annotate(has_not_expired_render=models.Exists(renders))

    def has_not_expired_render(self):
        qs = self._with_has_not_expired_render_annotation()
        return qs.filter(has_not_expired_render=True)

    def downloaded(self):
        return self.filter(source_file__isnull=False)

    def not_downloaded(self):
        return self.filter(source_file__isnull=True)

    def update_or_create_from_api(self, result):
        return self.update_or_create(arxiv_id=result['arxiv_id'],
                                     defaults=result)

    def update_or_create_from_arxiv_id(self, arxiv_id):
        """
        Query the arXiv API and create a Paper from it.

        Raises:
            `arxiv_vanity.scraper.query.PaperNotFoundError`: If paper does not exist on arxiv.
        """
        return self.update_or_create_from_api(query_single_paper(arxiv_id))

    def machine_learning(self):
        """
        Return only machine learning papers.
        """
        return self.filter(categories__overlap=settings.PAPERS_MACHINE_LEARNING_CATEGORIES)


class PaperManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def deleted(self):
        return super().get_queryset().filter(is_deleted=True)


class Paper(models.Model):
    # ArXiV fields
    arxiv_id = models.CharField(max_length=50, unique=True)
    arxiv_version = models.IntegerField()
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

    # arXiv Vanity fields
    source_file = models.ForeignKey(
        'SourceFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    is_deleted = models.BooleanField(default=False)

    objects = PaperManager.from_queryset(PaperQuerySet)()

    class Meta:
        get_latest_by = 'updated'
        ordering = ['-updated']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('paper_detail', args=(self.arxiv_id,))

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

    def is_renderable(self):
        """
        Returns whether it is possible to render this paper.
        """
        return self.source_file and self.source_file.is_renderable()

    def get_or_download_source_file(self):
        """
        Attempts to get the source file from a bulk data download, otherwise
        downloads it and creates it.
        """
        self.source_file = SourceFile.objects.get_or_download(self.arxiv_id)
        self.save()
        return self.source_file

    def render(self):
        """
        Make a new render of this paper. Will download the source file and save
        itself if it hasn't already.
        """
        if not self.source_file:
            self.get_or_download_source_file()
        if not self.source_file.is_renderable():
            raise PaperIsNotRenderableError("This paper is not renderable.")
        render = Render.objects.create(paper=self)
        render.run()
        return render


class RenderQuerySet(models.QuerySet):
    def running(self):
        return self.filter(state=Render.STATE_RUNNING)

    def succeeded(self):
        return self.filter(state=Render.STATE_SUCCESS)

    def failed(self):
        return self.filter(state=Render.STATE_FAILURE)

    def not_expired(self):
        """
        Renders which have occurred in the last PAPERS_EXPIRED_DAYS days.
        """
        return self.filter(is_expired=False)
    
    def expired(self):
        return self.filter(is_expired=True)

    def update_state(self):
        """
        Update the state of renders that have a container.
        """
        for render in self.exclude(state=Render.STATE_UNSTARTED).filter(container_is_removed=False):
            try:
                render.update_state()
            except:
                log_exception()
        return self

    def update_is_expired(self):
        """
        Set renders as expired if they were rendered more than PAPERS_EXPIRED_DAYS
        ago.
        """
        expired_delta = datetime.timedelta(days=settings.PAPERS_EXPIRED_DAYS)
        expired_date = timezone.now() - expired_delta
        qs = self.filter(is_expired=False, created_at__lte=expired_date)
        for render in qs:
            render.expire()
        return qs

    def force_expire(self):
        """
        Mark renders as expired even if they haven't. Useful for forcing
        re-rendering.
        """
        for render in self.iterator():
            render.expire()
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
    is_expired = models.BooleanField(default=False)
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
            self.paper.source_file.file.name,
            self.get_output_path(),
            webhook_url=self.get_webhook_url()
        ).id
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
            self.container_logs = str(container.logs(), 'utf-8')
        except docker.errors.NotFound:
            # Container has been removed for some reason, so mark it as
            # removed so we don't try to update its state again
            self.container_is_removed = True
            # Give it a failed state if the render was still running
            if self.state == Render.STATE_RUNNING:
                self.state = Render.STATE_FAILURE
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

        # Deleting containers on Hyper.sh often fails, so save here so we at
        # least save the state. If remove fails, this will get retried by
        # the update_render_state cron job.
        self.save()

        if container.status == 'exited':
            try:
                # Force, or Hyper.sh often throws a 500
                container.remove(force=True)
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

    def expire(self):
        """
        Mark render as expired.
        """
        self.is_expired = True
        self.save()
        try:
            self.delete_output()
        except FileNotFoundError:
            log_exception()

    def delete_output(self):
        """
        Delete output path.
        """
        storage_delete_path(default_storage, self.get_output_path())



class SourceFileBulkTarball(models.Model):
    """
    A tarball of sources that is listed in arXiv's bulk sources manifest.

    We keep track of these so we know which tarballs we have already
    downloaded. They're quite big so we don't want to get them every time.
    """
    filename = models.CharField(max_length=255, unique=True)

    content_md5sum = models.TextField()
    first_item = models.TextField()
    last_item = models.TextField()
    md5sum = models.TextField()
    num_items = models.IntegerField()
    seq_num = models.IntegerField()
    size = models.IntegerField()
    timestamp = models.TextField()
    yymm = models.TextField()

    def __str__(self):
        return self.filename

    def has_correct_number_of_files(self):
        """
        Number of items specified in the manifest matches how many we have
        in the database. If this is false, it suggests there was some error
        in downloading source files.
        """
        return self.num_items == self.sourcefile_set.count()


class SourceFileQuerySet(models.QuerySet):
    def get_or_download(self, arxiv_id):
        """
        Returns a source file for an arxiv ID if it exists (probably created
        from a bulk source download), otherwise downloads and creates it.
        """
        try:
            return self.get(arxiv_id=arxiv_id)
        except SourceFile.DoesNotExist:
            return self.download_and_create(arxiv_id)

    def download_and_create(self, arxiv_id):
        """
        Download the LaTeX source of this paper, save to storage, and create
        SourceFile.
        """
        file = download_source_file(arxiv_id)
        return self.create(
            arxiv_id=arxiv_id,
            file=file,
        )

    def filename_exists(self, fn):
        return self.filter(file=f'source-files/{fn}').exists()


class SourceFile(models.Model):
    """
    Represents a paper source file from arXiv.

    NOTE: This is a new system, not yet used by the `Paper` model. Initially,
    we are downloading arXiv's bulk papers into this model, then we can switch
    `Paper` to use this model.
    """
    arxiv_id = models.CharField(max_length=50, unique=True)
    file = models.FileField(upload_to='source-files/', unique=True)
    bulk_tarball = models.ForeignKey(
        SourceFileBulkTarball,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="If this source file is from arXiv's bulk download service, this is the tarball it was in. If null, this source file was downloaded individually."
    )

    objects = SourceFileQuerySet.as_manager()

    def __str__(self):
        return str(self.file)

    def is_pdf(self):
        return self.file.name.endswith('.pdf')

    def is_renderable(self):
        """
        Returns whether it is possible to render this file.
        """
        name = self.file.name
        return (name is not None
                and name.endswith('.gz')
                and not name.endswith('.ps.gz')
                and not name.endswith('.dvi.gz'))
