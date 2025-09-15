from . import views
from django.urls import path

urlpatterns = [
    path("",views.index,name="index"),
    path("blog",views.blog,name="blog"),
    path("posts",views.posts_filtered,name="posts_filtered"),
    path("signin",views.signin,name="signin"),
    path("signup",views.signup,name="signup"),
    path("logout",views.logout,name="logout"),
    path("create",views.create,name="create"),
    path("toggle_like/<int:id>",views.toggle_like,name='toggle_like'),
    path("profile/<int:id>",views.profile,name='profile'),
    path("profile/edit/<int:id>",views.profileedit,name='profileedit'),
    path("post/<int:id>",views.post,name="post"),
    path('post/<int:post_id>/manage_editors/', views.manage_editors, name='manage_editors'),
    path("post/<int:post_id>/assign_editor",views.assign_editor,name="assign_editor"),
    path("post/comment/<int:id>",views.savecomment,name="savecomment"),
    path("post/comment/delete/<int:id>",views.deletecomment,name="deletecomment"),
    path("post/edit/<int:id>",views.editpost,name="editpost"),
    path("post/delete/<int:id>",views.deletepost,name="deletepost"),
]