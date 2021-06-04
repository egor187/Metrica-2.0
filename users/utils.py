from collections import Counter


def get_player_calendar_with_week_day_number(game_session_objs_list):
    """
    :param game_session_obj: object of a model with game sessions of user with annotated played weekdays
    :return: dict(number of weekday : percentage of play for that day)
    """
    list_of_played_weekdays = [elem.weekday for elem in game_session_objs_list]  # "No-query" operation. Queryset already cached in variable
    counter = Counter(list_of_played_weekdays)
    result = {key: counter[key]/len(list_of_played_weekdays)*100 for key in counter.keys()}

    return result


def get_player_calendar_with_week_day_name(game_session_objs_list):
    """
    :param game_session_obj: object of a model with game sessions of user with annotated played weekdays
    :return: dict(name of weekday : percentage of play for that day)
    """
    list_of_played_weekdays = [elem.created_at.strftime('%A') for elem in
                               game_session_objs_list]  # "No-query" operation. Queryset already cached in variable
    counter = Counter(list_of_played_weekdays)

    #  result with percentage-count for each weekday
    result = {key: counter[key]/len(list_of_played_weekdays)*100 for key in counter.keys()}

    #  result just with int-count for each weekday
    return dict(counter)


def get_the_most_played_day(game_session_objs_list):
    list_of_played_weekdays = [elem.created_at.strftime('%A') for elem in
                               game_session_objs_list]  # "No-query" operation. Queryset already cached in variable
    counter = Counter(list_of_played_weekdays).most_common(1) #  list of tuple with obj and its count
    return counter[0][0]