import datetime

from django.db.models import Count, Sum, Max

from games.db_actions import stats_repr, get_game_id_by_name
from games.models import Games, GameSession, GameScores
from users.models import CustomUser
from users.db_actions import get_user_id_by_name


ALL_USERS_USERNAMES_LIST = CustomUser.objects.all().values_list('username', flat=True)
ALL_GAMES = Games.objects.all()
ALL_GAMES_NAME_LIST = Games.objects.all().values_list('name', flat=True)


def show_stats_message(game: str):
    """
    Return text message with current statistics for player by chosen metrica
    """
    if get_game_id_by_name(game):
        score_pairs = stats_repr(game)
        if isinstance(score_pairs, dict):
            result_msg = f"На {datetime.datetime.today().replace(microsecond=0)} " \
                         f"по игре '{game}' {'общие статы ВСЕХ игрокококов такие'}:\n"
            for user_name, score in score_pairs.items():
                result_msg += user_name + ': ' + str(score) + '\n'
            return result_msg
        return "Еще не шпилили"
    return "Нет такой игры в метрике"


def get_total_summary_for_user(username):
    if get_user_id_by_name(username):
        all_metrica = Games.objects.all().only('pk')
        queryset = all_metrica.objects.filter(
            sessions_scores_user_username=username
        ).annotate(
            summary_sessions=Count('sessions'),
            summary_scores=Sum('sessions__scores__score')
        )
        result = {
            game.name: {
                'summary_sessions': game.total_playes,
                'summary_score': game.summary_score
            } for game in queryset
        }
        return result
    return 'No such user'


def get_weekend_stats_for_user(username):
    now = datetime.datetime.now()
    week_before = datetime.timedelta(weeks=1)

    if get_user_id_by_name(username):
        all_metrica = Games.objects.all().only('pk')
        queryset = all_metrica.objects.filter(
            sessions_scores_user_username=username
        ).filter(
            sessions__created_at__gte=now-week_before
        ).annotate(
            summary_sessions=Count('sessions'),
            summary_scores=Sum('sessions__scores__score')
        )
        result = {
            game.name: {
                'summary_sessions': game.total_playes,
                'summary_score': game.summary_score
            } for game in queryset
        }
        return result
    return 'No such user'


def get_total_summary_by_game():
    all_metrica = Games.objects.all().only('pk')
    queryset = all_metrica.objects.annotate(
        summary_sessions=Count('sessions'),
        summary_scores=Sum('sessions__scores__score')
    )
    result = {
        game.name: {
            'summary_sessions': game.total_playes,
            'summary_score': game.summary_score
        } for game in queryset
    }
    return result


def get_weekly_metrica_for_users(username_list: list, weeks_before=0):
    """
    Return stats for each player about all registered metrics by game_session for about "weeks_before" kwarg
    :param username_list:
    :param weeks_before:
    :return: nested dict {user: [{game name in session: game score in session},]}
    """
    now = datetime.datetime.now()
    week_before = datetime.timedelta(weeks=weeks_before)
    result = {}
    for username in username_list:
        if get_user_id_by_name(username):
            if week_before:
                result[username] = list(
                    {
                        'game': session.game.name,
                        'summary_score': session.summary_score
                    } for session in GameSession.objects.filter(
                        created_at__gte=now - week_before,
                        is_private=False
                    ).filter(
                        scores__user__username=username
                    ).annotate(summary_score=Sum('scores__score'))
                )

            else:
                result[username] = list(
                    {
                        'game': session.game.name,
                        'summary_score': session.summary_score
                    } for session in GameSession.objects.filter(
                        scores__user__username=username
                    ).annotate(summary_score=Sum('scores__score'))
                )

        else:
            print('No such registered user in Metrica 2.0')
            continue

    return result


def humanable_stats_represent(username_list=ALL_USERS_USERNAMES_LIST, weeks_before=0):
    stats = get_weekly_metrica_for_users(username_list, weeks_before)
    stats_string = ''
    result_msg = ''
    result = {}
    total = {}

    for user, stats in stats.items():
        for session in stats:
            result[session['game']] = result.get(session['game'], 0) + session['summary_score']
        total[user] = total.get(user, []) + list(result.items())
        result = {}

    for name, stats in total.items():
        if stats:
            for elem in stats:
                stats_string += f"в игре '{elem[0]}' набрал {elem[1]}; \n"
        else:
            stats_string = 'ваще не играл'
        if weeks_before:
            result_msg += f"Игрок '{name}' за прошедшие {weeks_before} недель {stats_string} \n"
        else:
            result_msg += f"Игрок '{name}' за все время {stats_string} \n"
        stats_string = ''

    return result_msg[:4090] + "..."  # tg process only 4096 characters in sendMessage api


def top_3_week_players(game_name: str, period_in_weeks: int):
    now = datetime.datetime.now()
    before = datetime.timedelta(weeks=period_in_weeks)
    period = now - before

    if ALL_GAMES.filter(name=game_name):
        result = GameScores.objects.filter(
            game_session__game__name=game_name,
            game_session__created_at__gte=period
        ).order_by('-score')[:3]
        return result
    return "No such game registered in Metrica"


def top_3_week_players_repr_public_sessions(game_name: str, period_in_weeks):
    now = datetime.datetime.now()
    try:
        before = datetime.timedelta(weeks=int(period_in_weeks))
    except ValueError:
        return 'Incorrect period format: must be an integer. Try again.'
    period = now - before

    if ALL_GAMES.filter(name=game_name):
        query = GameScores.objects.filter(
            game_session__is_private=False,
            game_session__game__name=game_name,
            game_session__created_at__gte=period
        ).order_by('-score')[:3]

        top_players_list = query.values_list('user__username', 'score')
        msg = ''
        for elem in top_players_list:
            msg += f"'{str(elem[0])}' with score {str(elem[1])}, \n"
        str_repr = f"Top 3 players for public game sessions for game '{game_name}' by period in {period_in_weeks} " \
                   f"week(s) before is: {msg}"
        return str_repr
    return "No such game registered in Metrica"


def get_weekly_top_players_public_sessions(game_list=ALL_GAMES, period_in_weeks=1):
    """
    Return users with highest stats by game in specified period
    :param game_list:
    :param period_in_weeks:
    :return: nested dict {game_name: {'max_score': int(score), 'user': set(str(users),)}}
    """
    if period_in_weeks:
        now = datetime.datetime.now()
        before = datetime.timedelta(weeks=int(period_in_weeks))
        period = now - before
    else:
        period = datetime.date(2021, 1, 1)
    result = {}

    for game in game_list:
        max_score = GameScores.objects.filter(game_session__game=game,
                                              game_session__is_private=False,
                                              game_session__created_at__gte=period
                                              ).aggregate(Max('score'))['score__max']

        if max_score:
            result[game.name] = {
                'max_score': max_score,
                'user': set(list(
                    GameScores.objects.filter(
                        game_session__game=game, score=max_score
                    ).values_list('user__username', flat=True)))}

        else:
            continue

    return result


def get_weekly_top_players_public_sessions_repr(game_list=ALL_GAMES, period_in_weeks=1):
    """
    Convert 'top players' msg to human-friendly str message for publishing by telegram bot
    """
    stats = get_weekly_top_players_public_sessions(game_list, period_in_weeks)
    result_msg = f"За прошедшие '{period_in_weeks}' недель(ю)"
    for key, value in stats.items():
        result_msg += f"\nв игре '{key}' лучшим(и) игроками со счетом '{value['max_score']}' был(и): '{', '.join(value['user'])}';"

    return result_msg
