import datetime
from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.db.models import OuterRef, Subquery
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.cache import add_never_cache_headers, patch_cache_control
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, ListView
from .models import Paper, Render, PaperIsNotRenderableError
from .renderer import TooManyRendersRunningError
from ..scraper.arxiv_ids import (
    remove_version_from_arxiv_id,
    ARXIV_URL_RE,
    ARXIV_DOI_RE,
    ARXIV_VANITY_RE,
)
from ..scraper.query import PaperNotFoundError


def add_paper_cache_control(response, request=None):
    if request and "nocache" in request.GET:
        add_never_cache_headers(response)
    else:
        patch_cache_control(response, public=True, max_age=settings.PAPER_CACHE_SECONDS)
    return response


class HomeView(TemplateView):
    template_name = "papers/home.html"

    def dispatch(self, *args, **kwargs):
        res = super(HomeView, self).dispatch(*args, **kwargs)
        return add_paper_cache_control(res)


class PaperListView(ListView):
    model = Paper
    paginate_by = 100

    def get_queryset(self):
        qs = super(PaperListView, self).get_queryset()
        return qs.machine_learning().has_successful_render().order_by("-updated")

    def dispatch(self, *args, **kwargs):
        res = super(PaperListView, self).dispatch(*args, **kwargs)
        return add_paper_cache_control(res)


def paper_detail(request, arxiv_id):
    force_render = "render" in request.GET
    no_render = "no-render" in request.GET

    arxiv_id, version = remove_version_from_arxiv_id(arxiv_id)
    if version is not None:
        return redirect("paper_detail", arxiv_id=arxiv_id)

    # Get the requested paper
    try:
        paper = Paper.objects.get(arxiv_id=arxiv_id)
    # If it doesn't exist, fetch from arXiv API
    except Paper.DoesNotExist:
        # update_or_create to avoid the race condition where several people
        # hit a new paper at the same time
        try:
            paper, _ = Paper.objects.update_or_create_from_arxiv_id(arxiv_id)
        except PaperNotFoundError:
            raise Http404(f"Paper '{arxiv_id}' not found on arXiv")

    try:
        render_to_display = paper.get_render_to_display_and_render_if_needed(
            force_render=force_render,
            no_render=no_render,
        )
    # This will only get raised when no_render is true
    except Render.DoesNotExist:
        raise Http404("No render found for this paper, and not rendering")
    except PaperIsNotRenderableError:
        res = render(
            request,
            "papers/paper_detail_not_renderable.html",
            {"paper": paper},
            status=404,
        )
        return add_paper_cache_control(res, request)
    except TooManyRendersRunningError:
        res = render(
            request,
            "papers/paper_detail_too_many_renders.html",
            {"paper": paper},
            status=503,
        )
        add_never_cache_headers(res)
        return res

    # Switch response based on state
    if render_to_display.state == Render.STATE_RUNNING:
        res = render(
            request,
            "papers/paper_detail_rendering.html",
            {"paper": paper, "render": render_to_display},
            status=503,
        )
        add_never_cache_headers(res)
        return res

    elif render_to_display.state == Render.STATE_FAILURE:
        res = render(
            request, "papers/paper_detail_error.html", {"paper": paper}, status=500
        )
        return add_paper_cache_control(res, request)

    elif render_to_display.state == Render.STATE_SUCCESS:
        processed_render = render_to_display.get_processed_render()

        res = render(
            request,
            "papers/paper_detail.html",
            {
                "paper": paper,
                "render": render_to_display,
                "body": processed_render["body"],
                "links": processed_render["links"],
                "scripts": processed_render["scripts"],
                "styles": processed_render["styles"],
                "abstract": processed_render["abstract"],
                "first_image": processed_render["first_image"],
            },
        )
        return add_paper_cache_control(res, request)

    else:
        raise Exception(f"Unknown render state: {render_to_display.state}")


def paper_update(request, arxiv_id):
    arxiv_id, version = remove_version_from_arxiv_id(arxiv_id)
    if version is not None:
        return redirect("paper_update", arxiv_id=arxiv_id)

    try:
        _, _ = Paper.objects.update_or_create_from_arxiv_id(arxiv_id)
    except PaperNotFoundError:
        raise Http404(f"Paper '{arxiv_id}' not found on arXiv")
    return redirect("paper_detail", arxiv_id=arxiv_id)


@never_cache
def paper_render_state(request, arxiv_id):
    paper = get_object_or_404(Paper, arxiv_id=arxiv_id)
    try:
        r = paper.renders.latest()
    except Render.DoesNotExist:
        raise Http404()
    return JsonResponse({"state": r.state})


@csrf_exempt
@require_POST
def render_update_state(request, pk):
    r = get_object_or_404(Render, pk=pk, container_is_removed=False)
    r.update_state(exit_code=request.POST.get("exit_code"))
    r.delete_older_renders_if_successful()
    return HttpResponse()


def convert_query_to_arxiv_id(query):
    query = query.strip()
    for regex in [ARXIV_URL_RE, ARXIV_DOI_RE, ARXIV_VANITY_RE]:
        match = regex.search(query)
        if match:
            return match.group(1)


@never_cache
def paper_convert(request):
    if not request.GET.get("query"):
        return render(
            request,
            "papers/paper_convert_error.html",
            {
                "message": "No paper was given. Please enter something into the search box."
            },
        )
    arxiv_id = convert_query_to_arxiv_id(request.GET["query"])
    if not arxiv_id:
        return render(
            request,
            "papers/paper_convert_error.html",
            {
                "message": "Could not find arXiv ID in that URL. Are you sure it's an arxiv.org URL?",
                "query": request.GET["query"],
            },
        )
    arxiv_id, _ = remove_version_from_arxiv_id(arxiv_id)
    return redirect("paper_detail", arxiv_id=arxiv_id)


@cache_control(public=True, max_age=30)
def stats(request):
    past_30_days = Render.objects.filter(
        created_at__gt=datetime.datetime.today() - datetime.timedelta(days=30)
    )

    newest_renders = Render.objects.filter(paper=OuterRef("pk")).order_by("-created_at")
    papers = Paper.objects.annotate(
        last_render_state=Subquery(newest_renders.values("state")[:1])
    ).exclude(last_render_state=None)

    return render(
        request,
        "papers/stats.html",
        {
            "total_renders": int(Render.objects.count()),
            "successful_renders": int(
                Render.objects.filter(state=Render.STATE_SUCCESS).count()
            ),
            "failed_renders": int(
                Render.objects.filter(state=Render.STATE_FAILURE).count()
            ),
            "total_renders_30_days": int(past_30_days.count()),
            "successful_renders_30_days": int(
                past_30_days.filter(state=Render.STATE_SUCCESS).count()
            ),
            "failed_renders_30_days": int(
                past_30_days.filter(state=Render.STATE_FAILURE).count()
            ),
            "total_papers": int(papers.count()),
            "successful_papers": int(
                papers.filter(last_render_state=Render.STATE_SUCCESS).count()
            ),
            "failed_papers": int(
                papers.filter(last_render_state=Render.STATE_FAILURE).count()
            ),
        },
    )
