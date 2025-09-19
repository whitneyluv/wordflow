"""
Константы для приложения WordFlow

Этот файл содержит все константы, используемые в приложении,
для лучшей организации и централизованного управления.
"""

# Константы для пагинации
POSTS_PER_PAGE_INDEX = 12
POSTS_PER_PAGE_BLOG = 5
USER_POSTS_PREVIEW_COUNT = 3

# Варианты сортировки постов
SORT_NEWEST = 'newest'
SORT_LIKES = 'likes'
SORT_VIEWS = 'views'
SORT_COMMENTS = 'comments'

SORT_CHOICES = [
    (SORT_NEWEST, 'По дате (новые)'),
    (SORT_LIKES, 'По лайкам'),
    (SORT_VIEWS, 'По просмотрам'),
    (SORT_COMMENTS, 'По комментариям'),
]

# Константы для моделей
DEFAULT_LIKES = 0
DEFAULT_VIEWS = 0
MAX_POST_NAME_LENGTH = 600
MAX_CATEGORY_NAME_LENGTH = 100
MAX_COMMENT_LENGTH = 200
MAX_DELETED_MESSAGE_LENGTH = 100

# Константы для форм склонения
RUSSIAN_PLURAL_FORMS = {
    'comment': ('комментарий', 'комментария', 'комментариев'),
    'view': ('просмотр', 'просмотра', 'просмотров'),
    'like': ('лайк', 'лайка', 'лайков'),
    'post': ('пост', 'поста', 'постов'),
    'user': ('пользователь', 'пользователя', 'пользователей'),
    'category': ('категория', 'категории', 'категорий'),
}

# Настройки безопасности
MAX_LOGIN_ATTEMPTS = 5
LOGIN_COOLDOWN_MINUTES = 15

# Настройки файлов
MAX_IMAGE_SIZE_MB = 5
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']

# Сообщения для пользователей
MESSAGES = {
    'post_created': 'Пост успешно создан',
    'post_updated': 'Пост успешно обновлен',
    'post_deleted': 'Пост успешно удален',
    'comment_added': 'Комментарий добавлен',
    'comment_deleted': 'Комментарий удален',
    'no_permission': 'У вас нет прав для выполнения этого действия',
    'login_required': 'Для выполнения этого действия необходимо войти в систему',
    'invalid_data': 'Переданы некорректные данные',
    'server_error': 'Произошла ошибка сервера. Попробуйте позже.',
}

# HTTP статус коды
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500
