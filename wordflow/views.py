from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages, auth
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Post, Comment, PostEditor, GlobalEditor, Category
from .forms import PostForm, CustomUserCreationForm
from .constants import (
    POSTS_PER_PAGE_INDEX, POSTS_PER_PAGE_BLOG, USER_POSTS_PREVIEW_COUNT,
    SORT_NEWEST, SORT_LIKES, SORT_VIEWS, SORT_COMMENTS, MESSAGES
)
from .logging_config import auth_logger, post_logger, security_logger, main_logger


def index(request):
    """
    Главная страница с постами, сортировкой и фильтрацией по категориям
    """
    sort_by = request.GET.get('sort', SORT_NEWEST)
    category_filter = request.GET.get('category')
    page_number = request.GET.get('page', 1)

    # Получаем посты пользователя для превью
    user_posts = _get_user_posts_preview(request.user)

    # Получаем все посты с фильтрацией и сортировкой
    main_posts = _get_filtered_and_sorted_posts(category_filter, sort_by)

    # Пагинация
    paginator = Paginator(main_posts, POSTS_PER_PAGE_INDEX)
    page_obj = paginator.get_page(page_number)
    
    return render(request, "index.html", {
        'posts': user_posts,
        'top_posts': page_obj,
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'current_sort': sort_by,
        'current_category': category_filter,
        'user': request.user,
        'media_url': settings.MEDIA_URL
    })


def _get_user_posts_preview(user):
    """Возвращает превью постов пользователя"""
    if user.is_authenticated:
        return Post.objects.filter(user_id=user.id).order_by("-id")[:USER_POSTS_PREVIEW_COUNT]
    return Post.objects.none()


def _get_filtered_and_sorted_posts(category_filter, sort_by):
    """Получает отфильтрованные и отсортированные посты"""
    posts = Post.objects.all()

    # Фильтрация по категории
    if category_filter and category_filter.strip():
        if category_filter.isdigit():
            posts = posts.filter(category_obj_id=category_filter)
        else:
            posts = posts.filter(
                Q(category_obj__name__icontains=category_filter) | 
                Q(category__icontains=category_filter)
            )
    
    # Сортировка
    if sort_by == SORT_LIKES:
        posts = posts.annotate(num_likes=Count('liked_by', distinct=True)).order_by('-num_likes', '-id')
    elif sort_by == SORT_VIEWS:
        posts = posts.order_by('-views', '-id')
    elif sort_by == SORT_COMMENTS:
        posts = posts.annotate(num_comments=Count('comment', distinct=True)).order_by('-num_comments', '-id')
    else:  # SORT_NEWEST
        posts = posts.order_by('-id')
    
    return posts


def signup(request):
    """
    Регистрация нового пользователя
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_logger.info(f'Новый пользователь зарегистрирован: {user.username} (email: {user.email})')
            messages.success(request, f'Аккаунт успешно создан для {user.username}! Теперь вы можете войти в систему.')
            return redirect('signin')
        else:
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    if field == 'username':
                        if 'already exists' in str(error) or 'уже существует' in str(error):
                            messages.error(request, f"Пользователь с именем '{form.data.get('username')}' уже существует")
                        else:
                            messages.error(request, f"Имя пользователя: {error}")
                    elif field == 'email':
                        if 'already exists' in str(error) or 'уже существует' in str(error):
                            messages.error(request, f"Пользователь с email '{form.data.get('email')}' уже зарегистрирован")
                        elif 'разрешенных доменов' in str(error):
                            messages.error(request, f"Email должен быть с доменом gmail.com, mail.ru, yandex.ru и т.д.")
                        else:
                            messages.error(request, f"Email: {error}")
                    elif field == 'password1':
                        messages.error(request, f"Пароль: {error}")
                    elif field == 'password2':
                        messages.error(request, f"Подтверждение пароля: {error}")
                    else:
                        messages.error(request, f"{field_name}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, "signup.html", {'form': form})


def signin(request):
    """Вход пользователя в систему"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        try:
            user_exists = User.objects.get(username=username)
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth.login(request, user)
                auth_logger.info(f'Пользователь {username} успешно вошел в систему')
                return redirect("index")
            else:
                security_logger.warning(f'Неудачная попытка входа для пользователя {username}: неправильный пароль')
                messages.error(request, "Неправильный пароль")
                return redirect('signin')
        except User.DoesNotExist:
            security_logger.warning(f'Попытка входа с несуществующим именем пользователя: {username}')
            messages.error(request, "Пользователь с таким именем не существует")
            return redirect('signin')

    return render(request, "signin.html")


def logout(request):
    """Выход пользователя из системы"""
    if request.user.is_authenticated:
        username = request.user.username
        auth.logout(request)
        auth_logger.info(f'Пользователь {username} вышел из системы')
    return redirect('index')


def blog(request):
    """
    Страница блога со всеми постами
    """
    page_number = request.GET.get('page', 1)

    # Получаем посты пользователя для превью
    user_posts = _get_user_posts_preview(request.user)

    # Все посты по дате
    all_posts = Post.objects.all().order_by("-id")

    paginator = Paginator(all_posts, POSTS_PER_PAGE_BLOG)
    page_obj = paginator.get_page(page_number)
    
    return render(request, "blog.html", {
        'posts': user_posts,
        'recent_posts': page_obj,
        'page_obj': page_obj,
        'user': request.user,
        'media_url': settings.MEDIA_URL
    })


@login_required
def create(request):
    """
    Создание нового поста
    """
    # Проверка прав на создание постов
    if not Post.can_create_posts(request.user):
        messages.error(
            request, 
            "У вас нет прав для создания постов. "
            "Обратитесь к администратору для получения прав редактирования."
        )
        return redirect('index')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                post = _create_post_with_category(form, request.user)
                post_logger.info(f'Пользователь {request.user.username} создал новый пост: "{post.postname}" (ID: {post.id})')
                messages.success(request, "Пост успешно создан")
                return redirect('index')
            except Exception as e:
                post_logger.error(f'Ошибка при создании поста пользователем {request.user.username}: {str(e)}')
                messages.error(request, f"Ошибка при создании поста: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm()
    
    return render(request, "create.html", {
        'form': form,
        'categories': Category.objects.all()
    })


def _create_post_with_category(form, user):
    """Создает пост с обработкой категории"""
    post = form.save(commit=False)
    post.user = user

    category_choice = form.cleaned_data.get('category_choice')
    new_category = form.cleaned_data.get('new_category', '').strip()
    
    if new_category:
        category, created = Category.objects.get_or_create(name=new_category)
        post.category_obj = category
        post.category = new_category
    elif category_choice:
        post.category_obj = category_choice
        post.category = category_choice.name
    
    post.save()
    return post


def profile(request, id):
    profile_user = User.objects.get(id=id)
    authored_posts = Post.objects.filter(user_id=id)
    editable_posts = Post.objects.filter(editors=profile_user)

    global_editors = []
    available_users = []
    if request.user.is_superuser and request.user.id == id:
        global_editors = GlobalEditor.objects.filter(is_active=True).select_related('user')
        editor_user_ids = global_editors.values_list('user_id', flat=True)
        available_users = User.objects.exclude(id__in=editor_user_ids).exclude(is_superuser=True)
    
    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'posts': authored_posts,
        'editable_posts': editable_posts,
        'global_editors': global_editors,
        'available_users': available_users,
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
        user.last_name = lastname
        user.email = email
        user.save()
        return redirect('profile', id=id)

    return render(request, "profileedit.html", {'user': User.objects.get(id=id)})


@login_required
def manage_editors(request, post_id):
    """Управление редакторами поста"""
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для управления редакторами этого поста")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'add' and user_id:
            try:
                editor_user = User.objects.get(id=user_id)
                if editor_user != post.user:
                    editor_obj, created = PostEditor.objects.get_or_create(
                        post=post, 
                        user=editor_user,
                        defaults={'assigned_by': request.user}
                    )
                    if created:
                        messages.success(request, f"Пользователь {editor_user.username} назначен редактором")
                    else:
                        messages.info(request, f"Пользователь {editor_user.username} уже является редактором")
                else:
                    messages.error(request, "Автор поста не может быть назначен редактором")
            except User.DoesNotExist:
                messages.error(request, "Пользователь не найден")
        
        elif action == 'remove' and user_id:
            try:
                editor_user = User.objects.get(id=user_id)
                PostEditor.objects.filter(post=post, user=editor_user).delete()
                messages.success(request, f"Пользователь {editor_user.username} удален из редакторов")
            except User.DoesNotExist:
                messages.error(request, "Пользователь не найден")
    

    current_editors = post.editors.all()
    all_users = User.objects.exclude(id=post.user.id)
    available_users = all_users.exclude(id__in=current_editors.values_list('id', flat=True))
    
    return render(request, 'manage_editors.html', {
        'post': post,
        'current_editors': current_editors,
        'available_users': available_users,
    })


def activate(request, uidb64, token):
    """Активация аккаунта пользователя"""
    from django.utils.http import urlsafe_base64_decode
    from django.utils.encoding import force_str
    from .utils import account_activation_token
    
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Ваш аккаунт успешно активирован!')
        return render(request, 'registration/activation_complete.html')
    else:
        return render(request, 'registration/activation_invalid.html')


@login_required
def assign_editor_ajax(request, post_id):
    """AJAX назначение редактора"""
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)

        if request.user != post.user and not request.user.is_superuser:
            return JsonResponse({'success': False, 'message': 'Нет прав для назначения редакторов'})
        
        user_id = request.POST.get('user_id')
        try:
            editor_user = User.objects.get(id=user_id)
            if editor_user != post.user:
                editor, created = PostEditor.objects.get_or_create(
                    post=post, 
                    user=editor_user,
                    defaults={'assigned_by': request.user}
                )
                if created:
                    return JsonResponse({
                        'success': True, 
                        'message': f'Пользователь {editor_user.username} назначен редактором'
                    })
                else:
                    return JsonResponse({
                        'success': False, 
                        'message': f'Пользователь {editor_user.username} уже является редактором'
                    })
            else:
                return JsonResponse({'success': False, 'message': 'Автор не может быть редактором'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Пользователь не найден'})
    
    return JsonResponse({'success': False, 'message': 'Неверный запрос'})


@login_required
def toggle_like(request, id):
    """Переключает лайк на посте (добавляет или убирает)"""
    if request.method == 'POST':
        post = get_object_or_404(Post, id=id)
        is_liked = post.toggle_like(request.user)

        if is_liked:
            messages.success(request, f'❤️ Лайк успешно поставлен на пост "{post.postname}"!')
        else:
            messages.info(request, f'💔 Лайк убран с поста "{post.postname}"')
        
        # Для AJAX запросов возвращаем JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({
                'is_liked': is_liked,
                'likes_count': post.likes,
                'message': f'❤️ Лайк поставлен!' if is_liked else f'💔 Лайк убран!',
                'success': True
            })

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    else:
        return redirect('post', id=id)


def post(request, id):
    post = get_object_or_404(Post, id=id)

    if request.user.is_authenticated:
        post.add_view(request.user)
    else:
        session_key = f'viewed_post_{post.id}'

        if not request.session.get(session_key, False):
            post.views += 1
            post.save()
            request.session[session_key] = True
            timeout = getattr(settings, 'ANONYMOUS_VIEW_SESSION_TIMEOUT', 86400)
            request.session.set_expiry(timeout)

    return render(request, "post-details.html", {
        "user": request.user,
        'post': post,
        'recent_posts': Post.objects.all().order_by("-id")[:5],
        'media_url': settings.MEDIA_URL,
        'comments': Comment.objects.filter(post=post),
        'total_comments': Comment.objects.filter(post=post).count()
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

    if request.user != comment.user and request.user != comment.post.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для удаления этого комментария")

    comment.soft_delete()
    messages.success(request, "Комментарий удален")
    return redirect('post', id=comment.post.id)


@login_required
def reply_comment(request, comment_id):
    """Ответ на комментарий"""
    parent_comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Comment.objects.create(
                content=content,
                post=parent_comment.post,
                user=request.user,
                parent=parent_comment
            )
            messages.success(request, "Ответ добавлен")
        else:
            messages.error(request, "Комментарий не может быть пустым")
    
    return redirect('post', id=parent_comment.post.id)


@login_required
def toggle_comment_like(request, comment_id):
    """Переключение лайка комментария"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == 'POST':
        is_liked = comment.toggle_like(request.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'likes_count': comment.likes,
                'is_liked': is_liked,
                'message': f'❤️ Лайк поставлен!' if is_liked else f'💔 Лайк убран!',
                'success': True
            })
    
    return redirect('post', id=comment.post.id)


@login_required
def editpost(request, id):
    from .forms import PostEditForm
    from .models import Category
    post = get_object_or_404(Post, id=id)

    if not post.can_edit(request.user):
        return HttpResponseForbidden("У вас нет прав для редактирования этого поста")

    if request.method == 'POST':
        form = PostEditForm(request.POST, request.FILES, instance=post, user=post.user)
        if form.is_valid():
            try:
                post = form.save(commit=False)

                category_choice = form.cleaned_data.get('category_choice')
                new_category = form.cleaned_data.get('new_category', '').strip()
                
                if new_category:
                    category, created = Category.objects.get_or_create(name=new_category)
                    post.category_obj = category
                    post.category = new_category
                elif category_choice:
                    post.category_obj = category_choice
                    post.category = category_choice.name
                else:
                    post.category_obj = None
                    post.category = ''

                post.save()

                if request.user == post.user or request.user.is_superuser:
                    editors = form.cleaned_data.get('editors', [])
                    PostEditor.objects.filter(post=post).delete()
                    for editor in editors:
                        PostEditor.objects.create(
                            post=post,
                            user=editor,
                            assigned_by=request.user
                        )
                
                messages.success(request, "Пост успешно обновлен")
                return redirect('profile', id=request.user.id)
            except Exception as e:
                messages.error(request, f"Ошибка при редактировании поста: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostEditForm(instance=post, user=post.user)

    return render(request, "postedit.html", {
        'form': form,
        'post': post,
        'categories': Category.objects.all()
    })


@login_required
def deletepost(request, id):
    post = get_object_or_404(Post, id=id)

    if request.user != post.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для удаления этого поста")

    post.delete()
    messages.success(request, "Пост успешно удален")
    return redirect('profile', id=request.user.id)


@login_required
def admin_posts(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Только для администраторов")

    return render(request, "admin_posts.html", {
        'all_posts': Post.objects.all().order_by("-id"),
        'media_url': settings.MEDIA_URL,
    })


def get_popular_posts(limit=5):
    """Возвращает самые популярные посты по количеству просмотров"""
    return Post.objects.all().order_by("-views")[:limit]


def index_with_views(request):
    return render(request, "index.html", {
        'posts': Post.objects.filter(user_id=request.user.id).order_by("id").reverse(),
        'top_posts': Post.objects.all().order_by("-likes"),
        'popular_posts': get_popular_posts(5),
        'recent_posts': Post.objects.all().order_by("-id"),
        'user': request.user,
        'media_url': settings.MEDIA_URL
    })


@login_required
def assign_editor(request, post_id):
    """Назначить редактора к посту"""
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для назначения редакторов")
    
    if request.method == 'POST':
        editor_id = request.POST.get('editor_id')
        if editor_id:
            try:
                editor = User.objects.get(id=editor_id)
                editor_obj, created = PostEditor.objects.get_or_create(
                    post=post, 
                    user=editor,
                    defaults={'assigned_by': request.user}
                )
                if created:
                    messages.success(request, f"Редактор {editor.username} назначен к посту")
                else:
                    messages.info(request, f"{editor.username} уже является редактором этого поста")
            except User.DoesNotExist:
                messages.error(request, "Пользователь не найден")
    
    return redirect('post', id=post_id)


@login_required
def remove_editor(request, post_id, editor_id):
    """Убрать редактора с поста"""
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для управления редакторами")
    
    try:
        from .models import PostEditor
        editor_assignment = PostEditor.objects.get(post=post, user_id=editor_id)
        editor_name = editor_assignment.user.username
        editor_assignment.delete()
        messages.success(request, f"Редактор {editor_name} убран с поста")
    except PostEditor.DoesNotExist:
        messages.error(request, "Редактор не найден")
    
    return redirect('post', id=post_id)


@login_required
def manage_global_editors(request):
    """Управление глобальными редакторами (только для суперпользователей)"""
    if not request.user.is_superuser:
        return HttpResponseForbidden("Только для администраторов")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'add' and user_id:
            try:
                user = User.objects.get(id=user_id)
                if not user.is_superuser:
                    editor_obj, created = GlobalEditor.objects.get_or_create(
                        user=user,
                        defaults={'assigned_by': request.user, 'is_active': True}
                    )
                    if created:
                        messages.success(request, f"Пользователь {user.username} назначен глобальным редактором")
                    else:
                        editor_obj.is_active = True
                        editor_obj.save()
                        messages.success(request, f"Пользователь {user.username} снова активирован как редактор")
                else:
                    messages.error(request, "Суперпользователи не могут быть назначены редакторами")
            except User.DoesNotExist:
                messages.error(request, "Пользователь не найден")
        
        elif action == 'remove' and user_id:
            try:
                editor = GlobalEditor.objects.get(user_id=user_id, is_active=True)
                editor.is_active = False
                editor.save()
                messages.success(request, f"Пользователь {editor.user.username} удален из глобальных редакторов")
            except GlobalEditor.DoesNotExist:
                messages.error(request, "Редактор не найден")
    
    return redirect('profile', id=request.user.id)


def posts_filtered(request):
    """Страница с фильтрацией и сортировкой постов"""
    from .models import Category, Comment
    from django.db.models import Count
    
    posts = Post.objects.all()

    category_filter = request.GET.get('category')
    if category_filter:
        if category_filter.isdigit():
            posts = posts.filter(category_obj_id=category_filter)
        else:
            from django.db.models import Q
            posts = posts.filter(
                Q(category_obj__name__icontains=category_filter) | 
                Q(category__icontains=category_filter)
            )

    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'likes':
        posts = posts.order_by('-likes')
    elif sort_by == 'views':
        posts = posts.order_by('-views')
    elif sort_by == 'comments':
        posts = posts.annotate(comment_count=Count('comment')).order_by('-comment_count')
    else: 
        posts = posts.order_by('-id')
    
    return render(request, "posts_filtered.html", {
        'posts': posts,
        'categories': Category.objects.all(),
        'current_category': category_filter,
        'current_sort': sort_by,
        'media_url': settings.MEDIA_URL,
        'user': request.user
    })