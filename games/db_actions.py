import os
import uuid
import imghdr
import logging
from datetime import datetime

from django.conf import settings
from django.db.models import Sum

from dotenv import load_dotenv, find_dotenv

from users.models import CustomUser
from .models import Games, GameScores, GameSession
from .checkup import negative_score_check
from users.db_actions import get_username_by_id, is_users_exist_from_score_pairs
from users.db_actions import add_user_into_db_from_score_pairs
from users.db_actions import get_user_object_by_id
from games.utils import get_default_cover


load_dotenv(find_dotenv())
logger = logging.getLogger("Metrica_logger")


def get_game_id_by_name(name):
    """
    :param name: str()-repr of game name
    :return: id of the game from db. In case when game is not in db - return False
    """
    try:
        game_id = Games.objects.get(name=name).pk
    except Games.DoesNotExist:
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
    except Games.DoesNotExist:
        return False
    return game


def get_game_object_by_name(game_name):
    game_object = Games.objects.filter(name=game_name)
    if game_object:
        return game_object[0]
    return game_object


def get_user_list_for_current_game(user_list, current_user_pk, game_pk):
    """
    :param user_list:
    :param current_user_pk: CustomUser instance from Django sessions middleware (request.user)
    :param game_pk: Games instance from GameDetail CBV
    :return: list of users which played specific game with info about game sessions depending on ownership of that info
    """
    user_list_for_current_game = []
    for user in user_list:
        sessions = []
        for score in user.scores.filter(game_session__game__pk=game_pk):
            if current_user_pk != user.pk:
                if score.game_session.is_private:
                    user.played_public_games_count -= 1
                else:
                    sessions.append(score.game_session)
            else:
                sessions.append(score.game_session)

        if sessions:
            user_list_for_current_game.append(user)
    return user_list_for_current_game


def get_users_with_scores(current_user_pk, users_list, game_pk):
    """
    :param current_user_pk:
    :param users_list:
    :param game_pk:
    :return: user_list with dicts with calculated score and private_score (for private sessions) for each user.
    """
    result = []
    for user in users_list:
        if current_user_pk == user.pk:
            result.append(dict(
                name=user.username,
                score=GameScores.objects.filter(
                    game_session__game__pk=game_pk,
                ).filter(
                    user=user
                ).aggregate(Sum('score'))['score__sum'],
                private_score=GameScores.objects.filter(
                    game_session__game__pk=game_pk,
                    game_session__is_private=True,
                ).filter(
                    user=user
                ).aggregate(Sum('score'))['score__sum']
            )
            )
        else:
            result.append(dict(
                name=user.username,
                score=GameScores.objects.filter(
                    game_session__game__pk=game_pk,
                    game_session__is_private=False,
                ).filter(
                    user=user
                ).aggregate(Sum('score'))['score__sum']))
    return result


def add_game_into_db_single_from_bot(name, cover=None):
    """
    Insert new game into db
    :param cover: InMemoryUploadedFile (django wrapper on File object) game cover
    :param name: str()-name of the game
    :return: model object of new added game
    """

    dirs_by_date = datetime.now().strftime('/%Y/%m/%d/')
    file_name = f"{uuid.uuid4()}.jpg"
    full_path = f"{settings.MEDIA_UPLOADS_ROOT}/games_cover{dirs_by_date}"
    file_fp = f"{full_path}{file_name}"

    cover_path_for_field = f"/uploads/games_cover{dirs_by_date}{file_name}"
    default_cover_path_for_field = f"/uploads/games_cover{dirs_by_date}default_cover.jpg"
    default_cover_download_source = os.getenv('DEFAULT_GAME_COVER_SOURCE')

    os.makedirs(full_path, exist_ok=True)

    if not cover:
        get_default_cover(full_path, default_cover_download_source)
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
            logger.info("NON-image file cannot be processed."
                        "In case with new game - it will be saved without cover_art")

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

    each_user_in_db_check = is_users_exist_from_score_pairs(score_pairs)
    is_all_users_registered = all(each_user_in_db_check.values())

    if is_all_users_registered:
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

    else:
        result_msg_dict = {}
        for username, is_registered in each_user_in_db_check.items():
            if not is_registered:
                result_msg_dict.update({username: is_registered})
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


def add_tg_animation_scores(user_name, score):
    game_name = 'botyara'
    game = Games.objects.get_or_create(name=game_name)[0]
    game_session_object = add_game_session_into_db(game)
    user = CustomUser.objects.get_or_create(username=user_name)[0]
    GameScores.objects.create(
        game_session=game_session_object,
        user=user,
        score=score,
    )
