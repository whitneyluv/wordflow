from django.contrib import admin
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from .models import Post, Comment, PostView, PostLike, PostEditor, Category
# Register your models here.

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('postname', 'user', 'category', 'views', 'likes', 'time', 'get_editors_count')
    list_filter = ('category', 'user', 'time', 'category_obj')
    search_fields = ('postname', 'content', 'category', 'user__username')
    readonly_fields = ('views', 'likes', 'time')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('postname', 'content', 'user', 'category', 'category_obj', 'image')
        }),
        ('Статистика', {
            'fields': ('views', 'likes', 'time'),
            'classes': ('collapse',)
        }),
    )
    
    def get_editors_count(self, obj):
        return obj.editors.count()
    get_editors_count.short_description = 'Количество редакторов'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        super().save_model(request, obj, form, change)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('get_content_preview', 'user', 'post', 'time')
    list_filter = ('user', 'time', 'post__category')
    search_fields = ('content', 'user__username', 'post__postname')
    readonly_fields = ('time',)
    
    def get_content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    get_content_preview.short_description = 'Содержание'

@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'viewed_at')
    list_filter = ('viewed_at', 'post__category')
    search_fields = ('user__username', 'post__postname')

@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'liked_at')
    list_filter = ('liked_at', 'post__category')
    search_fields = ('user__username', 'post__postname')
    readonly_fields = ('liked_at',)

@admin.register(PostEditor)
class PostEditorAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'assigned_by', 'assigned_at')
    list_filter = ('assigned_at', 'assigned_by', 'post__category')
    search_fields = ('post__postname', 'user__username', 'assigned_by__username')
    readonly_fields = ('assigned_at',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_posts_count')
    search_fields = ('name',)
    
    def get_posts_count(self, obj):
        return obj.post_set.count()
    get_posts_count.short_description = 'Количество постов'

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_posts_count', 'get_comments_count')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    def get_posts_count(self, obj):
        return Post.objects.filter(user=obj).count()
    get_posts_count.short_description = 'Постов'
    
    def get_comments_count(self, obj):
        return Comment.objects.filter(user=obj).count()
    get_comments_count.short_description = 'Комментариев'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('session_key', 'expire_date', 'get_session_data_preview')
    list_filter = ('expire_date',)
    search_fields = ('session_key',)
    readonly_fields = ('session_key', 'session_data', 'expire_date')
    
    def get_session_data_preview(self, obj):
        """Показывает превью данных сессии"""
        if obj.session_data:
            return str(obj.get_decoded())[:100] + '...' if len(str(obj.get_decoded())) > 100 else str(obj.get_decoded())
        return 'Нет данных'
    get_session_data_preview.short_description = 'Данные сессии (превью)'

admin.site.site_header = 'WordFlow | ADMIN PANEL'
admin.site.site_title = 'WordFlow | BLOGGING WEBSITE'
admin.site.index_title= 'WordFlow | Site Administration'
