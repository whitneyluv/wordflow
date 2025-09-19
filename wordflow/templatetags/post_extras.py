from django import template
from ..models import Comment
from ..constants import RUSSIAN_PLURAL_FORMS
from ..utils import pluralize_russian, pluralize_russian_by_type

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
def comment_count_text(post):
    """Возвращает количество комментариев с правильным склонением"""
    count = Comment.objects.filter(post=post).count()
    return pluralize_russian_by_type(count, 'comment')

@register.filter
def views_count_text(views):
    """Возвращает количество просмотров с правильным склонением"""
    return pluralize_russian_by_type(views, 'view')

@register.filter
def likes_count_text(likes):
    """Возвращает количество лайков с правильным склонением"""
    return pluralize_russian_by_type(likes, 'like')

@register.filter
def can_delete_comment(comment, user):
    """
    Проверяет, может ли пользователь удалить комментарий
    
    Права на удаление:
    - Автор комментария
    - Автор поста
    - Администратор
    """
    if not user.is_authenticated:
        return False
    return (
        user == comment.user or 
        user == comment.post.user or 
        user.is_superuser
    )

@register.filter
def can_create_posts(user):
    """Проверяет, может ли пользователь создавать посты"""
    from ..models import Post
    return Post.can_create_posts(user)

@register.filter
def is_liked_by_comment(comment, user):
    """Проверяет, поставил ли пользователь лайк комментарию"""
    if user.is_authenticated:
        return comment.liked_by.filter(id=user.id).exists()
    return False

@register.filter
def can_edit_post(post, user):
    """Проверяет, может ли пользователь редактировать пост"""
    return post.can_edit(user)

# Функции склонения теперь в utils.py
