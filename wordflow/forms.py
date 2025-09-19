"""
Формы для приложения WordFlow

Этот файл содержит все формы для создания и редактирования
постов, регистрации пользователей и других операций.
"""

import re
from typing import Dict, Any, List
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from ckeditor.widgets import CKEditorWidget
from .models import Post, Category
from .constants import MAX_CATEGORY_NAME_LENGTH, ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_SIZE_MB
from .utils import safe_int, truncate_text


# Константы для валидации
ALLOWED_EMAIL_DOMAINS = [
    'gmail.com', 'mail.ru', 'yandex.ru', 'yandex.com', 'yahoo.com',
    'outlook.com', 'hotmail.com', 'rambler.ru', 'list.ru', 'bk.ru',
    'inbox.ru', 'ya.ru', 'icloud.com', 'protonmail.com'
]

MIN_PASSWORD_LENGTH = 8
MIN_UNIQUE_CHARS = 4
MIN_CHAR_TYPES = 3


def get_common_passwords() -> List[str]:
    """Возвращает список часто используемых паролей"""
    return [
        # Числовые последовательности
        '12345678', '87654321', '123456789', '987654321', '1234567890',
        '11111111', '22222222', '33333333', '44444444', '55555555',
        '66666666', '77777777', '88888888', '99999999', '00000000',
        '123123', '111111', '222222', '333333', '444444', '555555',
        '666666', '777777', '888888', '999999', '000000', '121212',
        
        # Простые пароли
        'password', 'password1', 'password123', 'pass', 'pass123',
        'qwerty', 'qwerty123', 'qwertyui', 'qwertyuiop', 'asdfgh',
        'asdfghjk', 'asdfghjkl', 'zxcvbn', 'zxcvbnm', 'admin',
        'administrator', 'root', 'user', 'guest', 'test', 'demo',
        
        # Русские пароли
        'пароль', 'пароль123', 'йцукен', 'йцукенг', 'фывапр',
        'фывапролд', 'ячсмить', 'ячсмитьбю', 'админ', 'администратор',
        
        # Имена
        'alexander', 'alexandra', 'andrew', 'anna', 'anton', 'maria',
        'michael', 'natasha', 'nikolai', 'olga', 'pavel', 'sergey',
        'александр', 'александра', 'андрей', 'анна', 'антон', 'мария',
    ]


def validate_password_strength(password: str) -> List[str]:
    """
    Проверяет надежность пароля и возвращает список ошибок
    
    Args:
        password: Пароль для проверки
        
    Returns:
        Список ошибок валидации
    """
    errors = []
    
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f'Пароль слишком короткий. Минимум {MIN_PASSWORD_LENGTH} символов.')
    
    if password.isdigit():
        errors.append('Пароль не может состоять только из цифр.')
    
    if password.isalpha():
        errors.append('Пароль не может состоять только из букв.')
    
    # Проверка типов символов
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
    
    char_types = sum([has_upper, has_lower, has_digit, has_special])
    if char_types < MIN_CHAR_TYPES:
        errors.append(
            f'Пароль должен содержать минимум {MIN_CHAR_TYPES} типа символов: '
            'заглавные буквы, строчные буквы, цифры и специальные символы.'
        )
    
    if len(set(password)) < MIN_UNIQUE_CHARS:
        errors.append(f'Пароль должен содержать минимум {MIN_UNIQUE_CHARS} уникальных символов.')
    
    # Проверка на простые последовательности
    sequences = ['123456', '654321', 'abcdef', 'fedcba', 'qwerty', 'asdfgh', 'zxcvbn']
    for seq in sequences:
        if seq in password.lower():
            errors.append('Пароль содержит простые последовательности символов.')
            break
    
    # Проверка на повторяющиеся паттерны
    for i in range(len(password) - 2):
        pattern = password[i:i+3]
        if password.count(pattern) > 1:
            errors.append('Пароль содержит повторяющиеся паттерны.')
            break
    
    # Проверка на распространенные пароли
    if password.lower() in [p.lower() for p in get_common_passwords()]:
        errors.append('Введённый пароль слишком широко распространён.')
    
    return errors

class PostForm(forms.ModelForm):
    content = forms.CharField(
        label='Содержание',
        widget=CKEditorWidget(config_name='basic'),
        required=True
    )
    
    category_choice = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Выберите категорию или создайте новую",
        required=False,
        label='Выбрать существующую категорию',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    new_category = forms.CharField(
        max_length=100,
        required=False,
        label='Или создать новую категорию',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название новой категории'})
    )
    
    class Meta:
        model = Post
        fields = ['postname', 'content', 'image']
        widgets = {
            'postname': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'required': True}),
        }
        labels = {
            'postname': 'Заголовок',
            'image': 'Изображение',
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()

        import re
        content_text = re.sub(r'<[^>]+>', '', content).strip()
        
        if not content_text:
            raise ValidationError('Пост должен содержать текст. Нельзя создавать посты с пустым содержанием.')
        
        return content
    
    def clean_image(self):
        """Валидация изображения поста"""
        image = self.cleaned_data.get('image')
        
        if not image:
            raise ValidationError(
                'Пост должен содержать изображение. '
                'Нельзя создавать посты без фотографий.'
            )
        
        # Проверяем размер файла
        if image.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise ValidationError(
                f'Размер изображения не должен превышать {MAX_IMAGE_SIZE_MB} МБ.'
            )
        
        # Проверяем расширение файла
        file_extension = image.name.split('.')[-1].lower() if '.' in image.name else ''
        if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(
                f'Разрешены только следующие форматы: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'
            )
        
        return image
    
    def clean(self):
        cleaned_data = super().clean()
        category_choice = cleaned_data.get('category_choice')
        new_category = cleaned_data.get('new_category', '').strip()

        if not category_choice and not new_category:
            raise ValidationError('Выберите существующую категорию или создайте новую.')

        if category_choice and new_category:
            cleaned_data['category_choice'] = None
        
        return cleaned_data

class PostEditForm(forms.ModelForm):
    content = forms.CharField(
        label='Содержание',
        widget=CKEditorWidget(config_name='basic'),
        required=True
    )
    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Редакторы'
    )
    
    category_choice = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Выберите категорию или создайте новую",
        required=False,
        label='Выбрать существующую категорию',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    new_category = forms.CharField(
        max_length=100,
        required=False,
        label='Или создать новую категорию',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название новой категории'})
    )
    
    class Meta:
        model = Post
        fields = ['postname', 'content', 'image']
        widgets = {
            'postname': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'postname': 'Заголовок',
            'image': 'Обновить изображение (необязательно)',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            self.fields['editors'].queryset = User.objects.exclude(id=user.id)

            if self.instance and self.instance.pk:
                self.fields['editors'].initial = self.instance.editors.all()
                if self.instance.category_obj:
                    self.fields['category_choice'].initial = self.instance.category_obj
    
    def clean_content(self) -> str:
        """Валидация содержания поста"""
        content = self.cleaned_data.get('content', '').strip()
        
        # Удаляем HTML теги для проверки наличия текста
        content_text = re.sub(r'<[^>]+>', '', content).strip()
        
        if not content_text:
            raise ValidationError(
                'Пост должен содержать текст. '
                'Нельзя создавать посты с пустым содержанием.'
            )
        
        return content
    
    def clean_image(self):
        """Валидация изображения поста"""
        image = self.cleaned_data.get('image')
        
        if not image and (not self.instance or not self.instance.image):
            raise ValidationError(
                'Пост должен содержать изображение. '
                'Нельзя создавать посты без фотографий.'
            )
        
        # Проверяем размер файла
        if image and image.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
            raise ValidationError(
                f'Размер изображения не должен превышать {MAX_IMAGE_SIZE_MB} МБ.'
            )
        
        # Проверяем расширение файла
        if image:
            file_extension = image.name.split('.')[-1].lower() if '.' in image.name else ''
            if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
                raise ValidationError(
                    f'Разрешены только следующие форматы: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'
                )
        
        return image
    
    def clean(self):
        cleaned_data = super().clean()
        category_choice = cleaned_data.get('category_choice')
        new_category = cleaned_data.get('new_category', '').strip()

        if not category_choice and not new_category:
            raise ValidationError('Выберите существующую категорию или создайте новую.')

        if category_choice and new_category:
            cleaned_data['category_choice'] = None
        
        return cleaned_data

class CustomUserCreationForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label='Email адрес',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Фамилия',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Ваш пароль должен содержать как минимум 8 символов, не должен быть слишком простым или широко распространенным, и не должен состоять только из цифр.'
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Имя пользователя',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_email(self) -> str:
        """Валидация email адреса"""
        email = self.cleaned_data.get('email')
        if not email:
            return email
            
        # Проверка формата email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(
                'Пожалуйста, укажите правильный email адрес (например: example@gmail.com)'
            )

        # Проверка разрешенных доменов
        domain = email.split('@')[-1].lower()
        if domain not in ALLOWED_EMAIL_DOMAINS:
            raise ValidationError(
                f'Используйте email с одним из разрешенных доменов: {", ".join(ALLOWED_EMAIL_DOMAINS)}'
            )

        # Проверка уникальности email
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        
        return email

    def clean_password1(self) -> str:
        """Валидация пароля с использованием вспомогательной функции"""
        password1 = self.cleaned_data.get('password1')
        if not password1:
            return password1
            
        # Используем нашу функцию для проверки надежности пароля
        errors = validate_password_strength(password1)
        
        # Дополнительная проверка Django валидатором
        try:
            validate_password(password1, self.instance)
        except ValidationError as error:
            for err in error.messages:
                if 'too common' in err.lower() and 'Введённый пароль слишком широко распространён.' not in errors:
                    errors.append('Введённый пароль слишком широко распространён.')
                elif 'similar' in err.lower():
                    errors.append('Пароль слишком похож на другую вашу личную информацию.')
        
        if errors:
            raise ValidationError(errors)
                
        return password1

    def clean_password2(self) -> str:
        """Валидация подтверждения пароля"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError('Пароли не совпадают.')
            
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.set_password(self.cleaned_data['password1'])
        user.is_active = True
        if commit:
            user.save()
        return user
