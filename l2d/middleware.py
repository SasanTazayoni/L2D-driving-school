from django.conf import settings


class ContentSecurityPolicyMiddleware:
    """
    Adds a Content-Security-Policy header listing where the site may load
    scripts, styles, fonts, images and frames from, and where forms may be
    sent. If a cross-site scripting bug ever let someone inject a script, the
    browser would refuse to run it.

    While CSP_ENFORCE is off, the policy is sent as
    Content-Security-Policy-Report-Only: browsers only log what they *would*
    block (in the developer console) without blocking anything, so the policy
    can be checked on the live site before it is switched on.

    The admin and its rich-text editor (CSP_EXCLUDED_PATHS) rely on inline
    scripts, so they are left out; they are only reachable by staff.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(tuple(settings.CSP_EXCLUDED_PATHS)):
            return response
        header = (
            'Content-Security-Policy' if settings.CSP_ENFORCE
            else 'Content-Security-Policy-Report-Only'
        )
        policy = '; '.join(
            f"{directive} {' '.join(sources)}"
            for directive, sources in settings.CONTENT_SECURITY_POLICY.items()
        )
        response.headers.setdefault(header, policy)
        return response
