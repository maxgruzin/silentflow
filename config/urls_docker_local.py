"""Serve copied media locally without changing the shared nginx service."""
from django.conf import settings
from django.conf.urls.static import static

from .urls import urlpatterns as application_urls
from .media_docker_local import serve_media

urlpatterns = static(settings.MEDIA_URL, view=serve_media, document_root=settings.MEDIA_ROOT) + application_urls
