from .settings_base import *


ALLOWED_HOSTS = [
    'a-metrica.herokuapp.com',
    ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME_HEROKU'),
        'USER': os.getenv('DB_USER_HEROKU'),
        'PASSWORD': os.getenv('DB_PASSWORD_HEROKU'),
        'HOST': os.getenv('DB_HOST_HEROKU'),
        'PORT': '5432',
    }
}