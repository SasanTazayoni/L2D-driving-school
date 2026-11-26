from django.http import HttpResponseForbidden
from django.shortcuts import render


# Django calls this with `exception` as a keyword argument, so the
# parameter must exist even though the page does not use it.
def handler404(request, exception):  # pylint: disable=unused-argument
    return render(request, '404.html', status=404)


def summernote_upload_disabled(request):
    """
    Replaces django-summernote's file upload endpoint, which by default
    accepts uploads from anyone. The site never displays uploaded files
    (review and profile text is rendered escaped), so uploads are refused.
    """
    return HttpResponseForbidden("File uploads are disabled.")
