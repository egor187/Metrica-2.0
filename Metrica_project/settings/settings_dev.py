import sys

from .settings_base import *

DEBUG = True


ALLOWED_HOSTS = [
    os.getenv('ALLOWED_HOST_PGROK'),
    'testserver',
    '127.0.0.1',
]

INSTALLED_APPS += [
    'debug_toolbar',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': '5432',
        'TEST': {
            'NAME': os.getenv('TEST_DB'),
            'USER': os.getenv('DB_USER')
        }
    }
}

# if testing (sys.argv contain 'test') db settings set to local db' sqlite3 and django connect to it to
# create tables for testings purpose
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

# Debug-toolbar settings
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
# Debug toolbar will be available for requests from this IPs
INTERNAL_IPS = [
    '127.0.0.1',
    ]

PROJECT_ROOT_URL = os.getenv('PROJECT_ROOT_URL_DEV')
