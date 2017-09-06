from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
from .models import Paper, Render


class PaperListView(ListView):
    model = Paper
    paginate_by = 50

    def get_queryset(self):
        qs = super(PaperListView, self).get_queryset()
        return qs.has_successful_render()


def paper_detail(request, arxiv_id):
    paper = get_object_or_404(Paper, arxiv_id=arxiv_id)
    try:
        r = paper.renders.succeeded().latest()
    except Render.DoesNotExist:
        raise Http404("Paper is not rendered")

    processed_render = r.get_processed_render()

    return render(request, "papers/paper_detail.html", {
        'paper': paper,
        'render': r,
        'body': processed_render['body'],
        'scripts': processed_render['scripts'],
        'styles': processed_render['styles'],
    })
