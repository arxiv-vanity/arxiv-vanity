import re
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import ListView
from .models import Paper, Render, PaperIsNotRenderableError


class PaperListView(ListView):
    model = Paper
    paginate_by = 50

    def get_queryset(self):
        qs = super(PaperListView, self).get_queryset()
        return qs.machine_learning().has_successful_render()


def render_error(request, paper, message, status=404):
    context = {"paper": paper, "message": message}
    return render(request, "papers/paper_detail_error.html", context,
                  status=status)

def render_not_renderable_error(request, paper):
    return render_error(request, paper,
                        "This paper doesn't have LaTeX source code, so it "
                        "can't be rendered as a web page.")


def paper_detail(request, arxiv_id):
    # Get the requested paper
    try:
        paper = Paper.objects.get(arxiv_id=arxiv_id)
    # If it doesn't exist, render it!
    except Paper.DoesNotExist:
        # update_or_create to avoid the race condition where several people
        # hit a new paper at the same time
        paper, created = Paper.objects.update_or_create_from_arxiv_id(arxiv_id)
        if created:
            try:
                paper.render()
            except PaperIsNotRenderableError:
                return render_not_renderable_error(request, paper)

    # First, try to get the latest succeeded paper -- this is always what
    # we'll want to render.
    try:
        r = paper.renders.succeeded().latest()
    except Render.DoesNotExist:
        # If there is no latest paper and the paper is not renderable, then
        # give up now.
        if not paper.is_renderable():
            return render_not_renderable_error(request, paper)
        # See if the paper has been rendered at all
        try:
            r = paper.renders.latest()
        except Render.DoesNotExist:
            # For some reason this paper hasn't been rendered. Probably
            # because it failed to download.
            # TODO(bfirsh): Fix papers in this state in a batch job.
            return render_error(request, paper,
                                "This paper temporarily failed to render. "
                                "Check back again soon – it will retry.")

        if r.state in (Render.STATE_UNSTARTED, Render.STATE_RUNNING):
            return render(request, "papers/paper_detail_rendering.html", {
                'paper': paper,
                'render': r,
            })

        # Fall back to error if there is no successful or running render
        return render_error(
            request, paper,
            "This paper failed to render. We are aware of the problem and "
            "will hopefully get it fixed soon!",
            status=500)

    processed_render = r.get_processed_render()

    return render(request, "papers/paper_detail.html", {
        'paper': paper,
        'render': r,
        'body': processed_render['body'],
        'scripts': processed_render['scripts'],
        'styles': processed_render['styles'],
    })


def paper_wait(request, arxiv_id):
    paper = get_object_or_404(Paper, arxiv_id=arxiv_id)
    try:
        r = paper.renders.latest()
    except Render.DoesNotExist:
        raise Http404('No render yet')
    if r.state == Render.STATE_UNSTARTED:
        raise Http404('No render yet')
    if r.state == Render.STATE_RUNNING:
        r.wait()
        r.update_state()
    return HttpResponse('')


ARXIV_ID_RE = re.compile(r'arxiv.org/[^\/]+/([\w\.]+)')


def convert_query_to_arxiv_id(query):
    match = ARXIV_ID_RE.search(query)
    if match:
        return match.group(1)


def paper_convert(request):
    if not request.GET.get('query'):
        return render(request, "papers/paper_convert_error.html", {
            "message": "No paper was given. Please enter something into the search box."
        })
    arxiv_id = convert_query_to_arxiv_id(request.GET['query'])
    if not arxiv_id:
        return render(request, "papers/paper_convert_error.html", {
            "message": "Could not find Arxiv ID in that URL. Are you sure it's an arxiv.org URL?"
        })
    return redirect("paper_detail", arxiv_id=arxiv_id)
