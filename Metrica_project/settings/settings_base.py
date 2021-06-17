from pathlib import Path
import os

from dotenv import load_dotenv, find_dotenv
from celery.schedules import crontab

load_dotenv(find_dotenv())

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    '127.0.0.1',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'Metrica_project',
    'users',
    'games',
    'telegram_bot',
  
    'bootstrap4',
    'anymail',
    'django_filters',
    'django_summernote',
    'swagger_render',
    'storages',
]

MIDDLEWARE = [
    'rollbar.contrib.django.middleware.RollbarNotifierMiddlewareOnly404',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'rollbar.contrib.django.middleware.RollbarNotifierMiddlewareExcluding404',
]

ROLLBAR = {
    'access_token': os.getenv('ROLLBAR_TOKEN'),
    'environment': 'development' if DEBUG else 'production',
    'branch': 'master',
    'root': BASE_DIR,
}

ROOT_URLCONF = 'Metrica_project.urls'

LOGIN_URL = 'users:login'
LOGOUT_REDIRECT_URL = 'users:users_index'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'Metrica_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTH_USER_MODEL = 'users.CustomUser'

# Internationalization
LANGUAGE_CODE = 'ru-ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static/dist'),
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'
MEDIA_UPLOADS_ROOT = os.path.join(MEDIA_ROOT, 'uploads')

ANYMAIL = {
    # (exact settings here depend on your ESP...)
    "MAILGUN_API_KEY": os.getenv('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": os.getenv('MAILGUN_DOMAIN'),  # your Mailgun domain, if needed
}

EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"  # or sendgrid.EmailBackend, or...
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')  # if you don't already have this in settings
SERVER_EMAIL = os.getenv('SERVER_EMAIL')  # ditto (default from-email for Django errors)

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} | {module} | {message}",
            "style": "{"
        },
        "verbose": {
            "format": "{levelname} | {asctime} | {module} | {process:d} | {thread:d} | {message}",
            "style": "{"
        },
    },
    'handlers': {
        'console_info': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': f'{BASE_DIR}/warning.log',
            'formatter': 'verbose'
        },
    },
    "loggers": {
        "Metrica_logger": {
            "handlers": ["console_info", "file_debug",],
            "level": "DEBUG",
        },
    }
}

# From Django 3.0, this setting is necessary for iframe (for SUMMERNOTE in our case)
X_FRAME_OPTIONS = 'SAMEORIGIN'

SUMMERNOTE_THEME = 'bs4'
SUMMERNOTE_CONFIG = {
    'summernote': {
        # As an example, using Summernote Air-mode
        'airMode': False,
    }
}

#  Url for inner requests between "bot-app" and others apps
PROJECT_ROOT_URL = os.getenv('PROJECT_ROOT_URL')

SWAGGER_YAML_FILENAME = '/docs/openapi.yml'

BOT_TOKEN = os.getenv("STATS_BOT_TOKEN_TEST")

# Celery settings
CELERY_BROKER_URL = 'redis://localhost'
CELERY_RESULT_BACKEND = 'redis://localhost'
CELERY_BEAT_SCHEDULE = {
    'send_stats_top_players_msg_every_monday': {
        'task': 'telegram_bot.tasks.weekly_stats_tg_notice_top_players',
        'schedule': crontab(day_of_week=4),
    },
}
CELERY_TIMEZONE = 'Europe/Moscow'
