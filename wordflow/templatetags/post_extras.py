from django import template
from ..models import Comment

register = template.Library()

@register.filter
def is_liked_by(post, user):
    """Проверяет, поставил ли пользователь лайк посту"""
    if user.is_authenticated:
        return post.liked_by.filter(id=user.id).exists()
    return False

@register.filter
def comment_count(post):
    """Возвращает количество комментариев к посту"""
    return Comment.objects.filter(post=post).count()

@register.filter
def can_delete_comment(comment, user):
    """Проверяет, может ли пользователь удалить комментарий (автор комментария, создатель поста или админ)"""
    if not user.is_authenticated:
        return False
    return user == comment.user or user == comment.post.user or user.is_superuser
