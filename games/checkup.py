def negative_score_check(score_pairs: dict):


    '''
    Checks for negative score values in incoming message and raise ValueError in this case
    :param score_pairs: dict() from income msg
    :return: ValueError
    '''
    if not all(list(map(lambda x: x >= 0, score_pairs.values()))):
        raise ValueError
