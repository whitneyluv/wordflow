from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from ckeditor.fields import RichTextField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


now = datetime.now()
time = now.strftime("%d %B %Y")

class Category(models.Model):
    """Модель для категорий постов"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Post(models.Model):
    postname = models.CharField(max_length=600)
    category = models.CharField(max_length=600)  # Временно оставляем как CharField
    category_obj = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)  # Новое поле для связи
    image = models.ImageField(upload_to='images/posts', blank=False, null=False)
    content = RichTextField()
    time = models.CharField(default=time, max_length=100, blank=True)
    likes = models.IntegerField(null=True, blank=True, default=0)
    views = models.IntegerField(default=0)  # Общее количество просмотров
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_posts')
    editors = models.ManyToManyField(User, through='PostEditor', through_fields=('post', 'user'), related_name='editable_posts', blank=True)
    viewed_by = models.ManyToManyField(User, through='PostView', related_name='viewed_posts')
    liked_by = models.ManyToManyField(User, through='PostLike', related_name='liked_posts')

    def __str__(self):
        return str(self.postname)

    def add_view(self, user):
        """Добавляет просмотр от пользователя"""
        if not self.viewed_by.filter(id=user.id).exists():
            PostView.objects.create(post=self, user=user)
            self.views += 1
            self.save()
    
    def toggle_like(self, user):
        """Переключает лайк от пользователя (добавляет или убирает)"""
        like_obj, created = PostLike.objects.get_or_create(post=self, user=user)
        if created:
            self.likes += 1
            self.save()
            return True
        else:
            like_obj.delete()
            self.likes -= 1
            self.save()
            return False
    
    def is_liked_by(self, user):
        """Проверяет, поставил ли пользователь лайк этому посту"""
        if user.is_authenticated:
            return self.liked_by.filter(id=user.id).exists()
        return False
    
    def can_edit(self, user):
        """Проверяет, может ли пользователь редактировать пост"""
        if not user.is_authenticated:
            return False
        return (user == self.user or 
                user.is_superuser or 
                self.editors.filter(id=user.id).exists())
    
    @staticmethod
    def can_create_posts(user):
        """Проверяет, может ли пользователь создавать посты"""
        if not user.is_authenticated:
            return False
        # Пользователь может создавать посты если:
        # 1. Он суперпользователь
        # 2. Он является глобальным редактором
        # 3. Он является редактором хотя бы одного поста
        # 4. Он уже создал хотя бы один пост (автор)
        from .models import GlobalEditor
        try:
            is_global_editor = GlobalEditor.objects.filter(user=user, is_active=True).exists()
        except:
            is_global_editor = False
            
        return (user.is_superuser or 
                is_global_editor or
                user.editable_posts.exists() or 
                user.authored_posts.exists())
    
    def get_category_name(self):
        """Возвращает название категории (новая модель или текстовое поле)"""
        if self.category_obj:
            return self.category_obj.name
        return self.category or "Без категории"


class PostView(models.Model):
    """Модель для отслеживания просмотров поста пользователями"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} viewed {self.post.postname}"


class PostEditor(models.Model):
    """Модель для назначения редакторов к постам"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_editors')

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} can edit {self.post.postname}"


class PostLike(models.Model):
    """Модель для отслеживания лайков поста пользователями"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

    def __str__(self):
        return f"{self.user.username} liked {self.post.postname}"


class Comment(models.Model):
    content = models.CharField(max_length=200)
    time = models.CharField(default=time, max_length=100, blank=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    likes = models.IntegerField(default=0)
    liked_by = models.ManyToManyField(User, through='CommentLike', related_name='liked_comments')
    is_deleted = models.BooleanField(default=False)
    deleted_message = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        if self.is_deleted:
            return f"{self.id}. [Удалено]"
        return f"{self.id}. {self.content[:20]}..."
    
    def toggle_like(self, user):
        """Переключает лайк от пользователя (добавляет или убирает)"""
        like_obj, created = CommentLike.objects.get_or_create(comment=self, user=user)
        if created:
            self.likes += 1
            self.save()
            return True
        else:
            like_obj.delete()
            self.likes -= 1
            self.save()
            return False
    
    def is_liked_by(self, user):
        """Проверяет, поставил ли пользователь лайк этому комментарию"""
        if user.is_authenticated:
            return self.liked_by.filter(id=user.id).exists()
        return False
    
    def soft_delete(self):
        """Мягкое удаление комментария с сообщением об удалении только если есть ответы"""
        if self.replies.exists():
            self.is_deleted = True
            self.deleted_message = "Удалено автором"
            self.content = ""
            self.save()
            return False
        else:
            self.delete()
            return True
    
    def get_display_content(self):
        """Возвращает контент для отображения"""
        if self.is_deleted:
            return self.deleted_message or "Удалено автором"
        return self.content


class CommentLike(models.Model):
    """Модель для отслеживания лайков комментариев пользователями"""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')

    def __str__(self):
        return f"{self.user.username} liked comment {self.comment.id}"


class GlobalEditor(models.Model):
    """Модель для глобальных редакторов, которые могут создавать посты"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='global_editor')
    assigned_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_global_editors')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Глобальный редактор"
        verbose_name_plural = "Глобальные редакторы"

    def __str__(self):
        return f"Глобальный редактор: {self.user.username}"