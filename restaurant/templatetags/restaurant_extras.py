from django import template

from restaurant.models import Profile

register = template.Library()


@register.filter
def add_class(field, css_class: str):
    existing = field.field.widget.attrs.get('class', '')
    classes = f'{existing} {css_class}'.strip()
    return field.as_widget(attrs={'class': classes})


@register.simple_tag(takes_context=True)
def is_admin(context):
    user = context['request'].user
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return hasattr(user, 'profile') and user.profile.role == Profile.ROLE_ADMIN
