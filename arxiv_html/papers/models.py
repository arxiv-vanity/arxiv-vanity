from django.conf import settings
from django.db import models
import os


class RenderError(Exception):
    pass


class RenderAlreadyStartedError(RenderError):
    """Render started when render has already been started."""


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


class Paper(models.Model):
    id = models.CharField(max_length=50, primary_key=True)

    objects = PaperQuerySet.as_manager()

    def __str__(self):
        return self.id

    def render(self):
        """
        Make a new render of this paper.
        """
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
        return settings.MEDIA_URL + self.get_output_path()

    def run(self):
        """
        Start running this render.
        """
        if self.state != Render.STATE_UNSTARTED:
            raise RenderAlreadyStartedError(f"Render {self.id} has already been started")

        # TODO: create render

        self.state = Render.STATE_RUNNING
        self.save()
