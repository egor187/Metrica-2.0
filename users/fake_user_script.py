import sys
import os
import django
import urllib.request

os.environ['DJANGO_SETTINGS_MODULE'] = 'Metrica_project.settings'  # set Django-needed settings module
django.setup()

from django.conf import settings
from faker import Faker
from faker.providers import internet, person, misc
from users.models import CustomUser


def create_random_image_file(path):
    urllib.request.urlretrieve('https://source.unsplash.com/random/400x400',
                               filename=settings.MEDIA_ROOT + '/' + path)


def fake_users(iteration):
    fake = Faker()
    fake.add_provider(internet)
    fake.add_provider(person)
    fake.add_provider(misc)

    username = fake.user_name()
    first_name = fake.first_name()
    last_name = fake.last_name()
    avatar_file_name = username + first_name + last_name + '.jpg'
    avatar_file_path = 'uploads/' + avatar_file_name

    create_random_image_file(avatar_file_path)

    for _ in range(iteration):
        CustomUser.objects.create_user(username=username, first_name=first_name,
                                       last_name=last_name, password='123456', email=fake.ascii_email(),
                                       avatar=avatar_file_path)
        print(username)
    print(f'{iteration} fake-users are created')


if __name__ == '__main__':
    fake_users(int(sys.argv[1]))
