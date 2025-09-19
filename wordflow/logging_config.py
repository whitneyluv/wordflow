"""
Конфигурация логгирования для приложения WordFlow

Этот файл содержит настройки логгирования для различных
компонентов приложения с разными уровнями детализации.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, Any

# Базовая директория проекта
BASE_DIR = Path(__file__).resolve().parent.parent

# Директория для логов
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

# Конфигурация логгирования
LOGGING_CONFIG: Dict[str, Any] = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '[{asctime}] {levelname} in {name}: {message} (in {pathname}:{lineno})',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'debug.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'detailed',
            'encoding': 'utf-8',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'error.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 10,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },
        'file_performance': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'performance.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 3,
            'formatter': 'detailed',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'wordflow': {
            'handlers': ['console', 'file_debug', 'file_error'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'wordflow.security': {
            'handlers': ['console', 'file_security', 'file_error'],
            'level': 'WARNING',
            'propagate': False,
        },
        'wordflow.performance': {
            'handlers': ['file_performance'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file_error'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['file_security'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
}


def setup_logging(debug: bool = False) -> None:
    """
    Настраивает логгирование для приложения
    
    Args:
        debug: Включить отладочный режим
    """
    import logging.config
    
    # Создаем директорию для логов если её нет
    LOGS_DIR.mkdir(exist_ok=True)
    
    # Настраиваем уровень логгирования в зависимости от режима
    if debug:
        LOGGING_CONFIG['loggers']['wordflow']['level'] = 'DEBUG'
        LOGGING_CONFIG['handlers']['console']['level'] = 'DEBUG'
    else:
        LOGGING_CONFIG['loggers']['wordflow']['level'] = 'INFO'
        LOGGING_CONFIG['handlers']['console']['level'] = 'INFO'
    
    # Применяем конфигурацию
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: str) -> logging.Logger:
    """
    Получает логгер с указанным именем
    
    Args:
        name: Имя логгера
        
    Returns:
        Настроенный логгер
    """
    return logging.getLogger(f'wordflow.{name}')


def get_security_logger() -> logging.Logger:
    """Получает логгер для событий безопасности"""
    return logging.getLogger('wordflow.security')


def get_performance_logger() -> logging.Logger:
    """Получает логгер для отслеживания производительности"""
    return logging.getLogger('wordflow.performance')


# Предустановленные логгеры для удобства
main_logger = get_logger('main')
auth_logger = get_logger('auth')
post_logger = get_logger('posts')
comment_logger = get_logger('comments')
security_logger = get_security_logger()
performance_logger = get_performance_logger()
