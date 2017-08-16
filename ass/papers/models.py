import datetime
from django.conf import settings
from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.files.base import ContentFile
import os
import requests
from .renderer import render_paper


class Paper(models.Model):
    # ArXiV fields
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

    # ASS fields
    source_file = models.FileField(upload_to='paper-sources/', null=True, blank=True)

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

    def download(self):
        """
        Download the LaTeX source of this paper and save to storage.

        You should call save() after running this method.
        """
        res = requests.get(self.get_source_url())
        res.raise_for_status()
        content = ContentFile(res.content)
        self.source_file.save(self.get_short_arxiv_id() + '.tar.gz', content)

    def render(self):
        """
        Make a new render of this paper. Will download the source file and save
        itself if it hasn't already.
        """
        if not self.source_file.name:
            self.download()
            self.save()
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
        return os.path.join('render-output', str(self.id))

    def run(self):
        """
        Start running this render.
        """
        if self.state != Render.STATE_UNSTARTED:
            raise RenderAlreadyStartedError("Render {} has already been started".format(self.id))
        self.container_id = render_paper(
            # HACK: needs relative "media" so it works in Docker
            os.path.join('media', self.paper.source_file.name),
            os.path.join('media', self.get_output_path())
        )
        self.state = Render.STATE_RUNNING
        self.save()
