import fake_entities


def generate_user():
    return fake_entities.User().create()


def generate_game():
    return fake_entities.Game().create()


def generate_game_session(game, date):
    return fake_entities.FakeGameSession(game=game, date=date).create()


def generate_game_score(user, game_session):
    return fake_entities.GameScore(user, game_session).create()


def generate_user_with_data(from_date, to_date):
    # This is the main generator function for the usual case: make a user with some game,
    # and sessions across some date range. User and games will have avatars and random names
    user = generate_user()
    game = generate_game()

    for date in fake_entities.get_dates_from_range(from_date, to_date):
        game_session = generate_game_session(game, date)
        generate_game_score(user, game_session)

    return user, game
