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
def comment_count_text(post):
    """Возвращает количество комментариев с правильным склонением"""
    count = Comment.objects.filter(post=post).count()
    return pluralize_russian(count, 'комментарий', 'комментария', 'комментариев')

@register.filter
def views_count_text(views):
    """Возвращает количество просмотров с правильным склонением"""
    return pluralize_russian(views, 'просмотр', 'просмотра', 'просмотров')

@register.filter
def can_delete_comment(comment, user):
    """Проверяет, может ли пользователь удалить комментарий (автор комментария, создатель поста или админ)"""
    if not user.is_authenticated:
        return False
    return user == comment.user or user == comment.post.user or user.is_superuser

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

def pluralize_russian(count, form1, form2, form5):
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} {form1}"
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return f"{count} {form2}"
    else:
        return f"{count} {form5}"
