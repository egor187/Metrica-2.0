from collections import Counter


def get_player_calendar(gs_obj):
    """
    :param gs_obj: object of a model with game sessions of user with annotated played weekdays
    :return: dict(number of weekday : percentage of play for that day)
    """
    list_of_played_weekdays = [elem.weekday for elem in gs_obj]  # "No-query" operation. Queryset already cached in variable
    counter = Counter(list_of_played_weekdays)
    result = {key: counter[key]/len(list_of_played_weekdays)*100 for key in counter.keys()}

    return result
