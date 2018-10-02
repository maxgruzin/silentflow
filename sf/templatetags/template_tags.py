from django import template
register = template.Library()


@register.filter(name='duration_format')
def duration_format(value):
    if value.hour:
        return value.strftime("%H:%M:%S")
    else:
        return value.strftime("%M:%S")
