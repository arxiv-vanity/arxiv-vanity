from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView
from .models import Paper, Render


class PaperListView(ListView):
    model = Paper
    paginate_by = 25


def paper_detail(request, pk):
    paper = get_object_or_404(Paper, pk=pk)
    try:
        r = paper.renders.latest()
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
