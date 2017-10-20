import base64
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .feedback import Feedback


@csrf_exempt
@require_POST
def submit_feedback(request):
    if request.method != "POST":
        return HttpResponse(code=400)
    arxiv_id = request.POST['arxivId']
    jpg_data_b64 = request.POST.get('jpgData')
    if jpg_data_b64:
        jpg_data = base64.b64decode(jpg_data_b64)
    else:
        jpg_data = None
    text = request.POST['text']

    feedback = Feedback(settings.GITHUB_ACCESS_TOKEN)
    issue_url = feedback.create_issue(arxiv_id, text, jpg_data)

    return JsonResponse({'issue_url': issue_url})
