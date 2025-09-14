from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, auth
from django.contrib.auth import authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponseForbidden
from .models import *


def index(request):
    return render(request, "index.html", {
        'posts': Post.objects.filter(user_id=request.user.id).order_by("id").reverse(),
        'top_posts': Post.objects.all().order_by("-likes"),
        'recent_posts': Post.objects.all().order_by("-id"),
        'user': request.user,
        'media_url': settings.MEDIA_URL
    })


def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(username=username).exists():
                messages.info(request, "Логин уже существует")
                return redirect('signup')
            if User.objects.filter(email=email).exists():
                messages.info(request, "Почта уже существует")
                return redirect('signup')
            else:
                User.objects.create_user(username=username, email=email, password=password).save()
                return redirect('signin')
        else:
            messages.info(request, "Пароль должен совпадать")
            return redirect('signup')

    return render(request, "signup.html")


def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect("index")
        else:
            messages.info(request, 'Логин или пароль неверны')
            return redirect("signin")

    return render(request, "signin.html")


def logout(request):
    auth.logout(request)
    return redirect('index')


def blog(request):
    return render(request, "blog.html", {
        'posts': Post.objects.filter(user_id=request.user.id).order_by("id").reverse(),
        'top_posts': Post.objects.all().order_by("-likes"),
        'recent_posts': Post.objects.all().order_by("-id"),
        'user': request.user,
        'media_url': settings.MEDIA_URL
    })


@login_required
def create(request):
    if request.method == 'POST':
        try:
            postname = request.POST['postname']
            content = request.POST['content']
            category = request.POST['category']
            image = request.FILES.get('image')

            if image:
                Post(postname=postname, content=content, category=category, image=image, user=request.user).save()
            else:
                Post(postname=postname, content=content, category=category, user=request.user).save()
        except Exception as e:
            messages.error(request, f"Ошибка при создании поста: {str(e)}")
            return redirect('create')
        return redirect('index')
    else:
        return render(request, "create.html")


def profile(request, id):
    return render(request, 'profile.html', {
        'profile_user': User.objects.get(id=id),
        'posts': Post.objects.filter(user_id=id),
        'media_url': settings.MEDIA_URL,
    })


@login_required
def profileedit(request, id):
    if request.user.id != id and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для редактирования этого профиля")

    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']

        user = User.objects.get(id=id)
        user.first_name = firstname
        user.email = email
        user.last_name = lastname
        user.save()
        return redirect('profile', id=id)

    return render(request, "profileedit.html", {
        'user': User.objects.get(id=id),
    })


@login_required
def increaselikes(request, id):
    if request.method == 'POST':
        post = Post.objects.get(id=id)
        post.likes += 1
        post.save()
    return redirect("index")


def post(request, id):
    post = get_object_or_404(Post, id=id)
    return render(request, "post-details.html", {
        "user": request.user,
        'post': post,
        'recent_posts': Post.objects.all().order_by("-id")[:5],
        'media_url': settings.MEDIA_URL,
        'comments': Comment.objects.filter(post_id=post.id),
        'total_comments': Comment.objects.filter(post_id=post.id).count()
    })


@login_required
def savecomment(request, id):
    post = get_object_or_404(Post, id=id)
    if request.method == 'POST':
        content = request.POST['message']
        Comment(post=post, user=request.user, content=content).save()
        return redirect("post", id=id)
    return redirect("post", id=id)


@login_required
def deletecomment(request, id):
    comment = get_object_or_404(Comment, id=id)

    # Проверка прав: автор комментария или суперпользователь
    if request.user != comment.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для удаления этого комментария")

    post_id = comment.post.id
    comment.delete()
    return redirect("post", id=post_id)


@login_required
def editpost(request, id):
    post = get_object_or_404(Post, id=id)

    # Проверка прав: автор поста или суперпользователь
    if request.user != post.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для редактирования этого поста")

    if request.method == 'POST':
        try:
            postname = request.POST['postname']
            content = request.POST['content']
            category = request.POST['category']
            image = request.FILES.get('image')

            post.postname = postname
            post.content = content
            post.category = category

            if image:
                post.image = image

            post.save()
            messages.success(request, "Пост успешно обновлен")
        except Exception as e:
            messages.error(request, f"Ошибка при редактировании поста: {str(e)}")

        return redirect('profile', id=request.user.id)

    return render(request, "postedit.html", {
        'post': post
    })


@login_required
def deletepost(request, id):
    post = get_object_or_404(Post, id=id)

    # Проверка прав: автор поста или суперпользователь
    if request.user != post.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для удаления этого поста")

    post.delete()
    messages.success(request, "Пост успешно удален")
    return redirect('profile', id=request.user.id)


# Дополнительная функция для суперпользователя - просмотр всех постов
@login_required
def admin_posts(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Только для администраторов")

    return render(request, "admin_posts.html", {
        'all_posts': Post.objects.all().order_by("-id"),
        'media_url': settings.MEDIA_URL,
    })