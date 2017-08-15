import os
from django.conf import settings
from django.views import static
from django.views.generic import ListView
from .models import Paper

class PaperListView(ListView):
    model = Paper
    paginate_by = 25


def paper_serve(request, id, path):
    if path == "":
        path = "index.html"
    document_root = os.path.join("renders/output/", id)
    return static.serve(request, path, document_root=document_root)
