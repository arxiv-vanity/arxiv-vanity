import datetime
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
import os
import urllib
from .renderer import render_paper


class Paper(models.Model):
    arxiv_id = models.CharField(max_length=200, unique=True)
    title = models.TextField()
    published = models.DateTimeField()
    updated = models.DateTimeField()
    summary = models.TextField()
    authors = JSONField()
    arxiv_url = models.URLField()
    pdf_url = models.URLField()
    primary_category = models.CharField(max_length=50)
    categories = ArrayField(models.CharField(max_length=50))
    comment = models.TextField(null=True, blank=True)
    doi = models.CharField(null=True, blank=True, max_length=100)
    journal_ref = models.TextField(null=True, blank=True, max_length=100)

    class Meta:
        get_latest_by = 'updated'
        ordering = ['-updated']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # TODO(bfirsh): use reverse()
        return "/papers/{}/".format(self.id)

    def get_short_arxiv_id(self):
        return self.arxiv_id.split('/')[-1]

    def get_source_url(self):
        return 'https://arxiv.org/e-print/' + self.get_short_arxiv_id()

    def get_downloaded_source_path(self):
        return 'renders/source/{}.tar.gz'.format(self.get_short_arxiv_id())

    def is_downloaded(self):
        return os.path.exists(self.get_downloaded_source_path())

    def download(self):
        download_path = self.get_downloaded_source_path()
        try:
            os.makedirs(os.path.dirname(download_path))
        except FileExistsError:
            pass
        urllib.request.urlretrieve(self.get_source_url(), download_path)

    def render(self):
        render = Render.objects.create(paper=self)
        render.run()


class RenderError(Exception):
    pass


class RenderAlreadyStartedError(RenderError):
    pass


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

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.paper.title

    def save(self, *args, **kwargs):
        super(Render, self).save(*args, **kwargs)

    def get_output_path(self):
        return 'renders/output/{}/'.format(self.id)

    def run(self):
        """
        Start running this render.
        """
        if self.state != Render.STATE_UNSTARTED:
            raise RenderAlreadyStartedError("Render {} has already been started".format(self.id))
        self.container_id = render_paper(
            self.paper.get_downloaded_source_path(),
            self.get_output_path()
        )
        self.state = Render.STATE_RUNNING
        self.save()
