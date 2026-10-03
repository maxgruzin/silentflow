from django.conf import settings
from . import seo


def site_metadata(request):
    return {
        'site_url': settings.SITE_URL,
        'canonical_url': seo.public_url(request.path),
        'indexable': seo.indexable(),
        'page_title': seo.DEFAULT_TITLE,
        'page_description': seo.DEFAULT_DESCRIPTION,
        'social_image': seo.social_image(),
        'site_schema': seo.site_schema(),
    }
