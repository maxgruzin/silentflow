from .seo import indexable


class IndexingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not indexable() or request.path.startswith('/control/') or response.status_code >= 400:
            response['X-Robots-Tag'] = 'noindex, nofollow'
        return response
