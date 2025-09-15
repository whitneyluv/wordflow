from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages, auth
from django.contrib.auth import authenticate, login
from django.conf import settings
from .models import Post, Comment, PostEditor
from .models import *


def index(request):
    from .models import Category, Comment
    from django.db.models import Count
    from django.core.paginator import Paginator
    
    # Получаем параметры сортировки и фильтрации
    sort_by = request.GET.get('sort', 'newest')
    category_filter = request.GET.get('category')
    page_number = request.GET.get('page', 1)
    
    # Debug: Print all GET parameters
    print(f"DEBUG INDEX: All GET parameters: {dict(request.GET)}")
    print(f"DEBUG INDEX: sort_by = '{sort_by}'")
    print(f"DEBUG INDEX: category_filter = '{category_filter}'")
    print(f"DEBUG INDEX: page_number = '{page_number}'")
    
    # Базовые запросы
    user_posts = Post.objects.filter(user_id=request.user.id).order_by("-id") if request.user.is_authenticated else Post.objects.none()
    
    # Основные посты с сортировкой
    main_posts = Post.objects.all()
    print(f"DEBUG INDEX: Total posts before filtering: {main_posts.count()}")
    
    # Фильтрация по категории
    if category_filter:
        print(f"DEBUG INDEX: Filtering posts by category: '{category_filter}'")
        if category_filter.isdigit():
            print(f"DEBUG INDEX: Using category_obj_id filter with ID: {category_filter}")
            main_posts = main_posts.filter(category_obj_id=category_filter)
            print(f"DEBUG INDEX: Posts with category_obj_id={category_filter}: {main_posts.count()}")
        else:
            print(f"DEBUG INDEX: Using category name filter with name: '{category_filter}'")
            main_posts = main_posts.filter(category__icontains=category_filter)
            print(f"DEBUG INDEX: Posts with category name containing '{category_filter}': {main_posts.count()}")
        
        print(f"DEBUG INDEX: Posts after filtering: {main_posts.count()}")
        if main_posts.exists():
            print(f"DEBUG INDEX: Filtered posts: {[p.postname for p in main_posts]}")
            print(f"DEBUG INDEX: Post categories: {[(p.postname, p.category, p.category_obj_id) for p in main_posts]}")
        else:
            print("DEBUG INDEX: No posts found after filtering")
            # Проверим все категории в базе
            all_categories = Category.objects.all()
            print(f"DEBUG INDEX: Available categories: {[(c.id, c.name) for c in all_categories]}")
            # Проверим все посты и их категории
            all_posts = Post.objects.all()
            print(f"DEBUG INDEX: All posts with categories: {[(p.postname, p.category, p.category_obj_id) for p in all_posts]}")
    
    # Сортировка
    print(f"DEBUG INDEX: Applying sorting: {sort_by}")
    if sort_by == 'likes':
        main_posts = main_posts.order_by('-likes', '-id')
        print(f"DEBUG INDEX: Sorted by likes")
    elif sort_by == 'views':
        main_posts = main_posts.order_by('-views', '-id')
        print(f"DEBUG INDEX: Sorted by views")
    elif sort_by == 'comments':
        main_posts = main_posts.annotate(comment_count=Count('comment')).order_by('-comment_count', '-id')
        print(f"DEBUG INDEX: Sorted by comments - found {main_posts.count()} posts")
    else:  # newest
        main_posts = main_posts.order_by('-id')
        print(f"DEBUG INDEX: Sorted by newest (default)")
    
    print(f"DEBUG INDEX: Final posts count: {main_posts.count()}")
    
    # Пагинация для основных постов
    paginator = Paginator(main_posts, 6)  # 6 постов на страницу
    page_obj = paginator.get_page(page_number)
    
    return render(request, "index.html", {
        'posts': user_posts[:3],  # Показываем только 3 поста пользователя
        'top_posts': page_obj,  # Используем пагинированные посты
        'page_obj': page_obj,
        'recent_posts': Post.objects.all().order_by("-id")[:5],
        'categories': Category.objects.all(),
        'current_sort': sort_by,
        'current_category': category_filter,
        'user': request.user,
        'media_url': settings.MEDIA_URL
    })


def signup(request):
    from .forms import CustomUserCreationForm
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Аккаунт успешно создан для {user.username}! Теперь вы можете войти в систему.')
            return redirect('signin')
        else:
            # Показываем конкретные ошибки валидации
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
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        
        # Проверяем существует ли пользователь
        try:
            user_exists = User.objects.get(username=username)
            # Если пользователь существует, проверяем пароль
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth.login(request, user)
                return redirect("index")
            else:
                messages.error(request, "Неправильный пароль")
                return redirect('signin')
        except User.DoesNotExist:
            messages.error(request, "Пользователь с таким именем не существует")
            return redirect('signin')

    return render(request, "signin.html")


def logout(request):
    auth.logout(request)
    return redirect('index')


def blog(request):
    from django.core.paginator import Paginator
    
    # Получаем параметр страницы
    page_number = request.GET.get('page', 1)
    
    # Посты пользователя (если авторизован)
    user_posts = Post.objects.filter(user_id=request.user.id).order_by("-id") if request.user.is_authenticated else Post.objects.none()
    
    # Все посты для основного списка (самые новые сначала)
    all_posts = Post.objects.all().order_by("-id")
    
    # Пагинация для всех постов
    paginator = Paginator(all_posts, 5)  # 5 постов на страницу
    page_obj = paginator.get_page(page_number)
    
    return render(request, "blog.html", {
        'posts': user_posts[:3],  # Показываем только 3 поста пользователя
        'recent_posts': page_obj,  # Используем пагинированные посты
        'page_obj': page_obj,
        'user': request.user,
        'media_url': settings.MEDIA_URL
    })


@login_required
def create(request):
    from .forms import PostForm
    from .models import Category
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                post = form.save(commit=False)
                post.user = request.user
                
                # Обработка категории
                category_name = form.cleaned_data.get('category', '').strip()
                if category_name:
                    category, created = Category.objects.get_or_create(name=category_name)
                    post.category_obj = category
                    post.category = category_name
                
                post.save()
                messages.success(request, "Пост успешно создан")
                return redirect('index')
            except Exception as e:
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


def profile(request, id):
    profile_user = User.objects.get(id=id)
    # Посты, которые пользователь создал
    authored_posts = Post.objects.filter(user_id=id)
    # Посты, которые пользователь может редактировать
    editable_posts = Post.objects.filter(editors=profile_user)
    
    return render(request, 'profile.html', {
        'profile_user': profile_user,
        'posts': authored_posts,
        'editable_posts': editable_posts,
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
    
    # Проверка прав: только автор поста или суперпользователь может назначать редакторов
    if request.user != post.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для управления редакторами этого поста")
    
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'add' and user_id:
            try:
                editor_user = User.objects.get(id=user_id)
                if editor_user != post.user:  # Автор не может быть редактором самого себя
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
    
    # Получаем текущих редакторов и всех пользователей
    current_editors = post.editors.all()
    all_users = User.objects.exclude(id=post.user.id)  # Исключаем автора
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
        
        # Проверка прав
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
        
        # Добавляем сообщение об успешном действии
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
    
    # Перенаправляем на ту же страницу, откуда пришел запрос
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    else:
        # Если нет HTTP_REFERER, перенаправляем на страницу поста
        return redirect('post', id=id)


def post(request, id):
    post = get_object_or_404(Post, id=id)

    # Добавляем просмотр при заходе на страницу поста
    if request.user.is_authenticated:
        # Для авторизованных пользователей используем систему PostView
        post.add_view(request.user)
    else:
        # Для анонимных пользователей используем сессии
        # Создаем уникальный ключ на основе ID поста
        session_key = f'viewed_post_{post.id}'
        
        # Проверяем, не просматривал ли уже этот пользователь этот пост
        if not request.session.get(session_key, False):
            post.views += 1
            post.save()
            # Отмечаем в сессии, что пост просмотрен
            request.session[session_key] = True
            # Устанавливаем время жизни сессии из настроек
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

    # Проверка прав: автор комментария, создатель поста или суперпользователь
    if request.user != comment.user and request.user != comment.post.user and not request.user.is_superuser:
        return HttpResponseForbidden("У вас нет прав для удаления этого комментария")

    post_id = comment.post.id
    comment.delete()
    messages.success(request, "Комментарий успешно удален")
    return redirect("post", id=post_id)


@login_required
def editpost(request, id):
    from .forms import PostEditForm
    from .models import Category
    post = get_object_or_404(Post, id=id)

    # Проверка прав: автор поста, назначенный редактор или суперпользователь
    if not post.can_edit(request.user):
        return HttpResponseForbidden("У вас нет прав для редактирования этого поста")

    if request.method == 'POST':
        form = PostEditForm(request.POST, request.FILES, instance=post, user=post.user)
        if form.is_valid():
            try:
                post = form.save(commit=False)
                
                # Обработка категории
                category_name = form.cleaned_data.get('category', '').strip()
                if category_name:
                    category, created = Category.objects.get_or_create(name=category_name)
                    post.category_obj = category
                    post.category = category_name
                else:
                    post.category_obj = None
                    post.category = ''

                post.save()
                
                # Обработка редакторов (только автор или админ может назначать)
                if request.user == post.user or request.user.is_superuser:
                    editors = form.cleaned_data.get('editors', [])
                    # Удаляем старых редакторов
                    PostEditor.objects.filter(post=post).delete()
                    # Добавляем новых редакторов
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
        # Инициализируем форму с данными поста
        form = PostEditForm(instance=post, user=post.user)

    return render(request, "postedit.html", {
        'form': form,
        'post': post,
        'categories': Category.objects.all()
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


# Новая функция для получения популярных постов по просмотрам
def get_popular_posts(limit=5):
    """Возвращает самые популярные посты по количеству просмотров"""
    return Post.objects.all().order_by("-views")[:limit]


# Обновляем индексную страницу с популярными постами
def index_with_views(request):
    return render(request, "index.html", {
        'posts': Post.objects.filter(user_id=request.user.id).order_by("id").reverse(),
        'top_posts': Post.objects.all().order_by("-likes"),
        'popular_posts': get_popular_posts(5),  # Добавляем популярные по просмотрам
        'recent_posts': Post.objects.all().order_by("-id"),
        'user': request.user,
        'media_url': settings.MEDIA_URL
    })


@login_required
def assign_editor(request, post_id):
    """Назначить редактора к посту"""
    post = get_object_or_404(Post, id=post_id)
    
    # Только автор поста или админ может назначать редакторов
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
    
    # Только автор поста или админ может убирать редакторов
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


def posts_filtered(request):
    """Страница с фильтрацией и сортировкой постов"""
    from .models import Category, Comment
    from django.db.models import Count
    
    posts = Post.objects.all()
    
    # Фильтрация по категории
    category_filter = request.GET.get('category')
    if category_filter:
        if category_filter.isdigit():
            posts = posts.filter(category_obj_id=category_filter)
        else:
            posts = posts.filter(category__icontains=category_filter)
    
    # Сортировка
    sort_by = request.GET.get('sort', 'newest')
    if sort_by == 'likes':
        posts = posts.order_by('-likes')
    elif sort_by == 'views':
        posts = posts.order_by('-views')
    elif sort_by == 'comments':
        posts = posts.annotate(comment_count=Count('comment')).order_by('-comment_count')
    else:  # newest
        posts = posts.order_by('-id')
    
    return render(request, "posts_filtered.html", {
        'posts': posts,
        'categories': Category.objects.all(),
        'current_category': category_filter,
        'current_sort': sort_by,
        'media_url': settings.MEDIA_URL,
        'user': request.user
    })