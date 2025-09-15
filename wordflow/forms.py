from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Post
from ckeditor.widgets import CKEditorWidget
import re

class PostForm(forms.ModelForm):
    content = forms.CharField(
        label='Содержание',
        widget=CKEditorWidget(config_name='basic')
    )
    
    class Meta:
        model = Post
        fields = ['postname', 'content', 'category', 'image']
        widgets = {
            'postname': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'postname': 'Заголовок',
            'category': 'Категория',
            'image': 'Изображение',
        }

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
    
    class Meta:
        model = Post
        fields = ['postname', 'content', 'category', 'image']
        widgets = {
            'postname': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'category': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'postname': 'Заголовок',
            'category': 'Категория',
            'image': 'Обновить изображение',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Исключаем автора поста из списка редакторов
            self.fields['editors'].queryset = User.objects.exclude(id=user.id)
            
            # Если редактируем существующий пост, устанавливаем текущих редакторов
            if self.instance and self.instance.pk:
                self.fields['editors'].initial = self.instance.editors.all()

class CustomUserCreationForm(UserCreationForm):
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
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Проверка базового формата email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise ValidationError('Пожалуйста, укажите правильный email адрес (например: example@gmail.com)')
            
            # Список разрешенных доменов
            allowed_domains = [
                'gmail.com', 'mail.ru', 'yandex.ru', 'yandex.com', 'yahoo.com',
                'outlook.com', 'hotmail.com', 'rambler.ru', 'list.ru', 'bk.ru',
                'inbox.ru', 'ya.ru', 'icloud.com', 'protonmail.com'
            ]
            
            domain = email.split('@')[-1].lower()
            if domain not in allowed_domains:
                raise ValidationError(
                    f'Используйте email с одним из разрешенных доменов: {", ".join(allowed_domains)}'
                )
            
            # Проверка на существование email
            if User.objects.filter(email=email).exists():
                raise ValidationError('Пользователь с таким email уже существует.')
        
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_active = True  # Пользователь сразу активен
        if commit:
            user.save()
        return user
