from django import template
import re

register = template.Library()

@register.filter
def highlight_text(text, query):
    """تظليل كلمات البحث في النص"""
    if not query:
        return text
    
    words = query.split()
    highlighted = text
    
    for word in words:
        if len(word) > 2:  # تجاهل الكلمات القصيرة
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            highlighted = pattern.sub(
                f'<span class="search-highlight">{word}</span>',
                highlighted
            )
    
    return highlighted

@register.filter
def extract_hashtags(text):
    """استخراج الهاشتاجات من النص"""
    hashtags = re.findall(r'#(\w+)', text)
    return list(set(hashtags))[:5]  # إرجاع 5 هاشتاجات فريدة فقط
