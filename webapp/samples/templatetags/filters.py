import base64

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def b64encode(value):
    string_bytes = value.encode("utf-8")
    base64_bytes = base64.b64encode(string_bytes)
    return base64_bytes.decode("ascii")

@register.filter
def get(d, key):
    return d.get(key)  # Safely get the value from the dictionary

@register.filter
def multiply(value, arg):
    return value * arg

@register.filter
def divide(value, arg):
    if arg == 0:
        return 0
    return value / arg
