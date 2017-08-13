from django.views.generic import ListView
from .models import Paper

class PaperListView(ListView):
    model = Paper
    paginate_by = 25
