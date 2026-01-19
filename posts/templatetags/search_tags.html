from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def highlight(text, search):
    """إبراز نص البحث في النص"""
    if not search or not text:
        return text
    
    search_lower = search.lower()
    text_str = str(text)
    
    highlighted = text_str
    for word in search_lower.split():
        start_tag = '<mark class="bg-yellow-200 px-1 rounded">'
        end_tag = '</mark>'
        
        # استبدال جميع الحالات (case-insensitive)
        import re
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        highlighted = pattern.sub(f"{start_tag}\\g<0>{end_tag}", highlighted)
    
    return mark_safe(highlighted)

@register.filter
def replace(value, arg):
    """استبدال نص في القالب"""
    if len(arg.split('|')) != 2:
        return value
    
    old, new = arg.split('|')
    return value.replace(old, new)
