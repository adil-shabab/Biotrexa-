from django import template
from bs4 import BeautifulSoup

register = template.Library()

@register.filter
def truncate_text(value, arg):
    """Truncate visible text to a specified number of characters, preserving HTML."""
    soup = BeautifulSoup(value, 'html.parser')
    text = soup.get_text()
    if len(text) <= arg:
        return value
    truncated_text = text[:arg] + '...'
    return truncated_text