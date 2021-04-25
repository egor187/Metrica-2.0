import django
import os
import requests
from faker import Faker
from PIL import Image
from django.conf import settings
import io
from datetime import date, timedelta, datetime

os.environ['DJANGO_SETTINGS_MODULE'] = 'Metrica_project.settings.settings_dev'  # set Django-needed settings module
django.setup()

from users.models import CustomUser
from games.models import Games, GameSession, GameScores

fake = Faker()


def create_random_image_file(path):
    response = requests.get('https://source.unsplash.com/random/400x400')
    image = Image.open(io.BytesIO(response.content))
    image.save(path)


def get_dates_from_range(from_date, to_date):
    days_in_range = (date.fromisoformat(to_date) - date.fromisoformat(from_date)).days
    amount = range(fake.random_int(0, days_in_range * 2))
    return list(map(lambda _: fake.date_time_between_dates(date.fromisoformat(from_date), date.fromisoformat(to_date)),
                    amount))


class Game(Games):
    class Meta:
        app_label = 'Metrica_project'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_name = fake.word()
        self.cover_art = {"full_path": f"{settings.MEDIA_UPLOADS_ROOT}/{self.game_name}_game_cover.jpg",
                          "uploads_path": f"uploads/{self.game_name}_game_cover.jpg"}

    def create(self):
        create_random_image_file(self.cover_art["full_path"])
        return Games.objects.create(name=self.game_name, cover_art=self.cover_art["uploads_path"])


class User(CustomUser):
    class Meta:
        app_label = 'Metrica_project'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = fake.user_name()
        self.first_name = fake.first_name()
        self.last_name = fake.last_name()
        self.password = '123456'
        self.email = fake.email()
        self.avatar = {
            "full_path": f"{settings.MEDIA_UPLOADS_ROOT}/{self.username}_avatar.jpg",
            "uploads_path": f"/uploads/{self.username}_avatar.jpg"
        }

    def create(self):
        create_random_image_file(self.avatar["full_path"])
        return CustomUser.objects.create_user(username=self.username, first_name=self.first_name,
                                              last_name=self.last_name,
                                              password=self.password, email=self.email,
                                              avatar=self.avatar["uploads_path"])


class FakeGameSession(GameSession):
    class Meta:
        app_label = 'Metrica_project'

    def __init__(self, game, date, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game = game
        self.date = date

    def create(self):
        return GameSession.objects.create(
            game=self.game,
            created_at=self.date
        )


class GameScore(GameScores):
    class Meta:
        app_label = 'Metrica_project'

    def __init__(self, user, game_session, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.game_session = game_session
        self.user = user
        self.score = fake.random.randrange(1, 5)

    def create(self):
        return GameScores.objects.create(game_session=self.game_session, user=self.user, score=self.score)
