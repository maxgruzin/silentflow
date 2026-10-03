"""Shared image sizes for templates and the optional pre-generation command."""
from sorl.thumbnail import get_thumbnail

PROFILES = {
    'card': ((320, 55), (640, 55), (960, 55)),
    'cover': ((600, 55), (960, 55)),
    'landscape': ((960, 55), (1920, 55), (2880, 55)),
}


def responsive_image(source, profile='card'):
    if not source:
        return None
    variants = []
    for width, quality in PROFILES[profile]:
        geometry = str(width) if profile == 'landscape' else f'{width}x{width}'
        variants.append(get_thumbnail(source, geometry, crop='center',
                                      upscale=False, format='AVIF', quality=quality))
    # Avoid duplicate width descriptors when the source is smaller than a variant.
    sources = {image.width: image.url for image in variants}
    fallback_width = 1920 if profile == 'landscape' else 960
    fallback_geometry = str(fallback_width) if profile == 'landscape' else f'{fallback_width}x{fallback_width}'
    fallback = get_thumbnail(source, fallback_geometry, crop='center',
                             upscale=False, format='JPEG', quality=85)
    return {
        'srcset': ', '.join(f'{url} {width}w' for width, url in sorted(sources.items())),
        'fallback': fallback,
    }
