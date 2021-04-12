import logging

from users.models import CustomUser


logger = logging.getLogger("Metrica_logger")

def get_username_by_id(id: int):
    """
    :param id: int(id) of requested user
    :return: str__repr of model object (username)
    """
    result = CustomUser.objects.get(id=id).username
    return result


def get_user_object_by_id(id):
    """
    :param user_id: int() id of the user in db
    :return: model.object (row from table) of the user.
    In case when game is not in db - return False
    """
    try:
        user_object = CustomUser.objects.get(id=id)
    except Exception:
        user_object = False
    return user_object


def get_user_id_by_name(name):
    """
    :param name: str() name of requested user
    :return: int()-id of requested user
    """
    result = CustomUser.objects.get(username=name).pk
    return result


def add_user_into_db_simple(username):
    user = CustomUser.objects.get_or_create(username=username)
    if user[1]:
        logger.info(f'New user "{username}" added to db. WELCOME!')
        return user[0].pk
    logger.info(f'User "{username}" already in db. Welcome back!')
    return


def add_user_into_db_from_score_pairs(score_pairs: dict):
    '''
    :param score_pairs: dict {"username": score:int}
    :return: list of id's new users added to db
    '''
    users_id_list = []
    for username in score_pairs.keys():
        user = CustomUser.objects.get_or_create(username=username)
        users_id_list.append(user[0].pk)
        if user[1]:
            logger.info(f'{username} added to DB')
        else:
            logger.info(f'{username} already in DB')
    return users_id_list
