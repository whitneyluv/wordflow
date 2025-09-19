from django import template
from .post_extras import pluralize_russian

register = template.Library()


@register.filter
def russian_plural(count, forms):
    """
    Фильтр для склонения слов по правилам русского языка
    
    Пример использования: {{ count|russian_plural:"комментарий,комментария,комментариев" }}
    
    Args:
        count: количество
        forms: строка с формами через запятую
    
    Returns:
        Склоненное слово с числом
    """
    forms_list = [form.strip() for form in forms.split(',')]
    
    if len(forms_list) != 3:
        return forms_list[0] if forms_list else ''
    
    try:
        count = int(count)
    except (ValueError, TypeError):
        return forms_list[0]
    
    return pluralize_russian(count, forms_list[0], forms_list[1], forms_list[2])


@register.filter
def russian_plural_word_only(count, forms):
    """
    Возвращает только склоненное слово без числа
    
    Пример: {{ count }} {{ count|russian_plural_word_only:"комментарий,комментария,комментариев" }}
    """
    forms_list = [form.strip() for form in forms.split(',')]
    
    if len(forms_list) != 3:
        return forms_list[0] if forms_list else ''
    
    try:
        count = int(count)
    except (ValueError, TypeError):
        return forms_list[0]
    
    # Используем ту же логику, но возвращаем только слово
    if count % 10 == 1 and count % 100 != 11:
        return forms_list[0]
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return forms_list[1]
    else:
        return forms_list[2]
