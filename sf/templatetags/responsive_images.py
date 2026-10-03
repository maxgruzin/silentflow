import logging

from django import template
from sf.images import responsive_image

register = template.Library()
logger = logging.getLogger(__name__)


@register.inclusion_tag('components/picture.html')
def picture(source, alt='', profile='card', sizes='100vw', eager=False, fit=''):
    try:
        image = responsive_image(source, profile)
    except (OSError, ValueError):
        logger.warning('Unable to generate responsive image for %s', source, exc_info=True)
        image = None
    if image and fit:
        fallback = image['fallback']
        # object-fit: cover can enlarge a wide image far beyond the screen width.
        # Supply the actual viewport-cover width; container heights are refined in JS.
        ratio = fallback.width / fallback.height
        sizes = f'max(100vw, {ratio * 100:.2f}vh)'
    return {'image': image, 'alt': alt, 'sizes': sizes, 'eager': eager, 'fit': fit}
