from .settings_base import *
import sys

DEBUG = True


ALLOWED_HOSTS = [
    os.getenv('ALLOWED_HOST_PGROK'),
    'testserver',
    '127.0.0.1',
]

INSTALLED_APPS += [
    'debug_toolbar',
]

# Debug toolbar will be available for requests from this IPs
INTERNAL_IPS = [
    '127.0.0.1',
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

# if testing (sys.argv contain 'test') db settings set to
# 'local db' sqlite3 and django connect to it to
# create tables for testings purpose
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

# Debug toolbar will be available for requests from this IPs
INTERNAL_IPS = [
    '127.0.0.1',
    ]
