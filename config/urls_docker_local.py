"""Serve copied media locally without changing the shared nginx service."""
from django.conf import settings
from django.conf.urls.static import static

from .urls import urlpatterns as application_urls

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + application_urls
