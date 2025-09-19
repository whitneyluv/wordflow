"""
Утилитарные функции для приложения WordFlow

Этот файл содержит общие утилитарные функции,
используемые в различных частях приложения.
"""

import logging
from typing import Optional, Dict, Any
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.http import HttpRequest
from .constants import RUSSIAN_PLURAL_FORMS

# Настройка логгинга
logger = logging.getLogger(__name__)


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    """
    Генератор токенов для активации аккаунта
    """
    def _make_hash_value(self, user: User, timestamp: int) -> str:
        return (
            str(user.pk) + str(timestamp) +
            str(user.is_active)
        )


account_activation_token = AccountActivationTokenGenerator()


def send_activation_email(request: HttpRequest, user: User) -> bool:
    """
    Отправляет email для активации аккаунта
    
    Args:
        request: HTTP запрос
        user: Пользователь
    
    Returns:
        bool: True если email отправлен успешно
    """
    try:
        current_site = get_current_site(request)
        mail_subject = 'Активируйте ваш аккаунт WordFlow'
        message = render_to_string('registration/activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        to_email = user.email
        email = EmailMessage(
            mail_subject, message, to=[to_email]
        )
        email.send()
        logger.info(f"Activation email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send activation email to {user.email}: {str(e)}")
        return False


def pluralize_russian(count: int, form1: str, form2: str, form5: str) -> str:
    """
    Склоняет слова по правилам русского языка
    
    Args:
        count: количество
        form1: форма для 1 (комментарий)
        form2: форма для 2-4 (комментария)
        form5: форма для 5+ (комментариев)
    
    Returns:
        Склоненное слово с числом
    """
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} {form1}"
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return f"{count} {form2}"
    else:
        return f"{count} {form5}"


def pluralize_russian_by_type(count: int, word_type: str) -> str:
    """
    Упрощенная функция склонения по типу слова
    
    Args:
        count: количество
        word_type: тип слова ('comment', 'view', 'like')
    
    Returns:
        Склоненное слово с числом
    """
    if word_type in RUSSIAN_PLURAL_FORMS:
        forms = RUSSIAN_PLURAL_FORMS[word_type]
        return pluralize_russian(count, forms[0], forms[1], forms[2])
    return f"{count} {word_type}"


def get_client_ip(request: HttpRequest) -> str:
    """
    Получает IP-адрес клиента
    
    Args:
        request: HTTP запрос
    
    Returns:
        IP-адрес клиента
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '0.0.0.0'


def safe_int(value: Any, default: int = 0) -> int:
    """
    Безопасное преобразование в целое число
    
    Args:
        value: Значение для преобразования
        default: Значение по умолчанию
    
    Returns:
        Целое число
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Обрезает текст до указанной длины
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина
        suffix: Суффикс для обрезанного текста
    
    Returns:
        Обрезанный текст
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix