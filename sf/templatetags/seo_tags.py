import json

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def structured_data(context):
    graph = list(context['site_schema'])
    if context.get('release_schema'):
        graph.append(context['release_schema'])
    payload = json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False)
    # JSON is inside a script element: prevent catalogue text closing that element.
    payload = payload.translate({ord('<'): r'\u003C', ord('>'): r'\u003E', ord('&'): r'\u0026'})
    return format_html('<script type="application/ld+json">{}</script>', mark_safe(payload))
