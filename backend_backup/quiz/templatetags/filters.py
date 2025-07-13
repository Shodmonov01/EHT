from django import template

register = template.Library()

@register.filter
def get_questions(categories_dict, category):
    return categories_dict.get(category, [])

@register.filter
def get(dictionary, key):
    return dictionary.get(key)