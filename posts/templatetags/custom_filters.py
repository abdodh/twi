# في مجلد posts (أو أي تطبيق)، أنشئ:
# posts/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    استبدل substring بآخر
    الاستخدام: {{ value|replace:"old,new" }}
    """
    if len(arg.split(',')) != 2:
        return value
    old, new = arg.split(',')
    return value.replace(old, new)

@register.filter
def remove(value, arg):
    """إزالة substring من النص"""
    return value.replace(arg, '')

@register.filter
def truncate_chars(value, arg):
    """تقليم النص بعد عدد محدد من الحروف"""
    try:
        length = int(arg)
    except ValueError:
        return value
    
    if len(value) <= length:
        return value
    
    return value[:length] + '...'
