import os
from bs4 import BeautifulSoup
from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views import static
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
    filename = os.path.join("renders/output/", str(r.pk), "index.html")
    with open(filename) as fh:
        soup = BeautifulSoup(fh)
    styles = soup.head.find_all('style')
    scripts = soup.head.find_all('script')
    return render(request, "papers/paper_detail.html", {
        "paper": paper,
        "render": r,
        "styles": ''.join(e.prettify() for e in styles),
        "scripts": ''.join(e.prettify() for e in scripts),
        "body": soup.body.encode_contents(),
    })


def paper_serve_static(request, pk, path):
    render = Paper.objects.get(pk=pk).renders.latest()
    if path == "":
        path = "index.html"
    document_root = os.path.join("renders/output/", str(render.pk))
    return static.serve(request, path, document_root=document_root)
