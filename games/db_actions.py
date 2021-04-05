from datetime import datetime
from django.db.models import Sum
from django.conf import settings
from users.models import CustomUser
from .models import Games, GameScores, GameSession
from .checkup import negative_score_check
from users.db_actions import get_username_by_id
from users.db_actions import add_user_into_db_from_score_pairs
from users.db_actions import get_user_object_by_id
import uuid
import os
import django.db.utils
import imghdr
import django.core.files.uploadedfile
from games.utils import get_default_cover
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def get_game_id_by_name(name):
    """
    :param name: str()-repr of game name
    :return: id of the game from db. In case when game is not in db - return False
    """
    try:
        game_id = Games.objects.get(name=name).pk
    except Exception:
        return False
    return game_id


def get_game_names_list():
    """
    :return: list() of names of all games in db
    """
    queryset = Games.objects.all()
    _list = [elem.name for elem in queryset]
    return _list


def get_game_object_by_id(game_id):
    """
    :param game_id: int() id of the game in db
    :return: model.object (row from table) of the game.
    In case when game is not in db - return False
    """
    try:
        game = Games.objects.get(id=game_id)
    except Exception:
        return False
    return game


def get_game_object_by_name(game_name):
    game_object = Games.objects.filter(name=game_name)
    if game_object:
        return game_object[0]
    return game_object


def add_game_into_db_single_from_bot(name, cover=None):
    """
    Insert new game into db
    :param cover: InMemoryUploadedFile (django wrapper on File object) game cover
    :param name: str()-name of the game
    :return: model object of new added game
    """
    dirs_by_date = datetime.now().strftime('\\%Y\\%m\\%d\\')
    file_name = f"{uuid.uuid4()}.jpg"
    full_path = f"{settings.MEDIA_UPLOADS_ROOT}\\games_cover{dirs_by_date}"
    file_fp = f"{full_path}{file_name}"

    cover_path_for_field = f"\\uploads\\games_cover{dirs_by_date}{file_name}"
    default_cover_path_for_field = f"\\uploads\\games_cover{dirs_by_date}default_cover.jpg"
    default_cover_download_source = os.getenv('DEFAULT_GAME_COVER_SOURCE')

    os.makedirs(full_path, exist_ok=True)

    get_default_cover(full_path, default_cover_download_source)

    if not cover:
        game = Games.objects.create(name=name, cover_art=default_cover_path_for_field)
        return game

    else:
        file_bytes = cover.read()
        if imghdr.what('', file_bytes) is not None:
            with open(file_fp, 'wb') as f:
                f.write(file_bytes)
                f.close()
                game = Games.objects.create(name=name, cover_art=cover_path_for_field)
                return game

        elif imghdr.what('', file_bytes) is None:
            print(
                "NON-image file cannot be processed. "
                "In case with new game - it will be saved without cover_art"
            )
            game = Games.objects.create(name=name, cover_art=default_cover_path_for_field)
            return game


def add_game_session_into_db(game):
    """
    Insert new game session object (row) into db
    :param game: model.object (row from db Games)
    :return: id of new game session object
    """
    date = datetime.now()
    game_session_object = GameSession.objects.create(
        game=game,
        created_at=date,
    )
    return game_session_object


def add_scores(game_name, score_pairs: dict):
    """
    Insert row (object) in table (model) GameScores from parsed income msg.
    :param game_name: str(name of the game)
    :param score_pairs: dict(str(username): int(score))
    :return: dict(str(username): sum(int(score)))
    """
    try:
        negative_score_check(score_pairs)
    except ValueError:
        return "Negative score is impossible"

    game = get_game_object_by_name(game_name)
    if not game:
        return f"Game '{game_name}' isn't tracked by Metrica! Please, register this game first."
    game_session_object = add_game_session_into_db(game)
    users_ids = add_user_into_db_from_score_pairs(score_pairs)
    result_msg_dict = dict()

    for user_id in users_ids:
        user = get_user_object_by_id(user_id)
        username = user.username
        GameScores.objects.create(
            game_session=game_session_object,
            user=user,
            score=score_pairs[username],
        )
        result_msg_dict[username] = \
            GameScores.objects.filter(game_session__game=game).filter(user=user).aggregate(Sum('score'))['score__sum']
    return result_msg_dict


def stats_repr(game):
    """
    :param game: str(name of the game)
    :return: sum of all scores all-played users in 'game': dict(str(username): sum(int(score)))
    """
    game_id = get_game_id_by_name(game)
    game_object = get_game_object_by_id(game_id)
    if not game_id:
        return f'В игру "{game}" Вы еще не играли. Статистика отсутствует.'
    users_ids = [i.id for i in CustomUser.objects.filter(scores__game_session__game=game_object).distinct()]
    result_msg_dict = dict()
    for user_id in users_ids:
        user = get_user_object_by_id(user_id)
        username = get_username_by_id(user_id)
        result_msg_dict[username] = \
            GameScores.objects.filter(
                game_session__game=game_object
            ).filter(user=user).aggregate(Sum('score'))['score__sum']
    return result_msg_dict
