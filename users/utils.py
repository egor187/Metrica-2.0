import io
from collections import Counter

import django.core.files.uploadedfile
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile

from PIL import Image


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
    if game_session_objs_list:
        list_of_played_weekdays = [elem.created_at.strftime('%A') for elem in
                                   game_session_objs_list]  # "No-query" operation. Queryset already cached in variable
        counter = Counter(list_of_played_weekdays).most_common(1) #  list of tuple with obj and its count
        return counter[0][0]
    return


def avatar_double_reducer(avatar: django.core.files.uploadedfile.InMemoryUploadedFile):
    """
    Reduce given Django InMemoryUploadedFile in a half
    :param avatar: django.core.files.uploadedfile.InMemoryUploadedFile
    :return: InMemoryUploadedFile
    """
    user_avatar_filename = avatar.name
    buffer = io.BytesIO()
    reduced_user_avatar = Image.open(io.BytesIO(avatar.read())).reduce(2)  # Reduce file size in twice
    reduced_user_avatar.save(fp=buffer, format='JPEG')  # save reduced file in bytes stream object to buffer for
    # further implementation of InMemoryUploadedFile (Django wrapper on sends through form file)

    file_from_buffer = buffer.getvalue()  # access to buffer for getting reduced file
    stream_file = ContentFile(file_from_buffer)  # Django file wrapper to read streams objects

    in_memory_uploaded_file = InMemoryUploadedFile(
        file=stream_file,
        field_name=None,
        name=user_avatar_filename,
        content_type='image/jpeg',
        size=len(stream_file),
        charset=None
    )

    return in_memory_uploaded_file
