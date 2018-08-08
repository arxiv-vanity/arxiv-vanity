from django.conf import settings
from django.db import models
import os


class RenderError(Exception):
    pass


class RenderAlreadyStartedError(RenderError):
    """Render started when render has already been started."""


class RenderQuerySet(models.QuerySet):
    def running(self):
        return self.filter(state=Render.STATE_RUNNING)

    def succeeded(self):
        return self.filter(state=Render.STATE_SUCCESS)

    def failed(self):
        return self.filter(state=Render.STATE_FAILURE)


class Render(models.Model):
    STATE_UNSTARTED = 'unstarted'
    STATE_RUNNING = 'running'
    STATE_SUCCESS = 'success'
    STATE_FAILURE = 'failure'

    ID_TYPE_ARXIV = 'arxiv'
    ID_TYPE_SUBMISSION = 'submission'

    id_type = models.CharField(max_length=20, choices=(
        (ID_TYPE_ARXIV, 'arXiv'),
        (ID_TYPE_SUBMISSION, 'Submission'),
    ))
    paper_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=20, default=STATE_UNSTARTED, choices=(
        (STATE_UNSTARTED, 'Unstarted'),
        (STATE_RUNNING, 'Running'),
        (STATE_SUCCESS, 'Success'),
        (STATE_FAILURE, 'Failure'),
    ))
    logs = models.TextField(null=True, blank=True)

    objects = RenderQuerySet.as_manager()

    class Meta:
        get_latest_by = 'created_at'

    def __str__(self):
        return self.id

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
        if self.state != Render.STATE_SUCCESS:
            return None
        return settings.MEDIA_URL + self.get_output_path()

    def run(self):
        """
        Start running this render.
        """
        # TODO: start render
