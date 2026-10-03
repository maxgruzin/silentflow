"""Single-range media responses for local player testing, never production."""
import re

from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.decorators.http import require_safe
from django.views.static import serve


@require_safe
def serve_media(request, path, document_root=None):
    if not settings.DEBUG:
        raise Http404
    # Keep Django's path safety, MIME detection and conditional request handling.
    response = serve(request, path, document_root=document_root)
    if response.status_code != 200:
        return response
    response['Accept-Ranges'] = 'bytes'
    if request.method != 'GET':
        return response
    if_range = request.headers.get('If-Range')
    if if_range and if_range != response.get('Last-Modified'):
        return response
    match = re.fullmatch(r'bytes=(\d*)-(\d*)', request.headers.get('Range', ''))
    if not match:
        # Multiple ranges and unsupported units can be ignored with a full 200.
        return response
    size = int(response['Content-Length'])
    first, last = match.groups()
    start = int(first) if first else max(0, size - int(last or 0))
    end = min(int(last), size - 1) if first and last else size - 1
    if start > end or start >= size:
        response.close()
        return HttpResponse(status=416, headers={'Content-Range': f'bytes */{size}'})
    stream = response.file_to_stream
    stream.seek(start)

    def chunks():
        remaining = end - start + 1
        while remaining:
            chunk = stream.read(min(65536, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk

    response.streaming_content = chunks()
    response.status_code = 206
    response['Content-Range'] = f'bytes {start}-{end}/{size}'
    response['Content-Length'] = end - start + 1
    return response
