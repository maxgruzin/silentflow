from django import template
from urllib.parse import urlsplit
register = template.Library()


@register.filter(name='duration_format')
def duration_format(value):
    if value is None:
        return ''
    if value.hour:
        return value.strftime("%H:%M:%S")
    else:
        return value.strftime("%M:%S")


@register.filter
def safe_web_url(value):
    """Only render navigable HTTP(S) links from catalogue content."""
    value = str(value or '').strip()
    try:
        parsed = urlsplit(value)
    except ValueError:
        return ''
    return value if parsed.scheme.lower() in {'http', 'https'} and parsed.netloc else ''
