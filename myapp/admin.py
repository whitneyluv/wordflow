from django.contrib import admin
from .models import Post,Comment
# Register your models here.

admin.site.register(Post)
admin.site.register(Comment)



admin.site.site_header = 'WordFlow | ADMIN PANEL'
admin.site.site_title = 'WordFlow | BLOGGING WEBSITE'
admin.site.index_title= 'WordFlow | Site Administration'
