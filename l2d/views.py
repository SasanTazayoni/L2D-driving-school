from django.http import HttpResponseForbidden
from django.shortcuts import render


# Django calls this with `exception` as a keyword argument, so the
# parameter must exist even though the page does not use it.
def handler404(request, exception):  # pylint: disable=unused-argument
    return render(request, '404.html', status=404)


def robots_txt(request):
    """
    robots.txt, with the sitemap's full address built from the request so it
    always matches the domain the site is actually served on.
    """
    return render(request, 'robots.txt', content_type='text/plain')


def summernote_upload_disabled(request):
    """
    Replaces django-summernote's file upload endpoint, which by default
    accepts uploads from anyone. The site never displays uploaded files
    (review and profile text is rendered escaped), so uploads are refused.
    """
    return HttpResponseForbidden("File uploads are disabled.")
