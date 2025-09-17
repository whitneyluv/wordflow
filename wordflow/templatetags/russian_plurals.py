from django import template

register = template.Library()

@register.filter
def russian_plural(count, forms):
    forms_list = forms.split(',')
    if len(forms_list) != 3:
        return forms_list[0] if forms_list else ''
    
    count = int(count)
    
    if count % 10 == 1 and count % 100 != 11:
        return forms_list[0]
    elif count % 10 in [2, 3, 4] and count % 100 not in [12, 13, 14]:
        return forms_list[1]
    else:
        return forms_list[2]
