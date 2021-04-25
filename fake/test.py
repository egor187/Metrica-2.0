from datetime import datetime
from faker import Faker
from fake_entities import get_dates_from_range
from generator import generate_user, generate_game, generate_game_session, generate_game_score, generate_user_with_data


def test_generate_user():
    user = generate_user()
    print(f"User generated successfully: {user.username}")
    assert True is True


def test_generate_game():
    game = generate_game()
    print(f"Game generated successfully: {game}")
    assert True is True


def test_generate_game_session():
    game = generate_game()
    game_session = generate_game_session(game, datetime.now())
    print(f"Game session generated successfully: {game_session}")
    assert True is True


def test_get_dates_from_range():
    Faker.seed(1)
    result = get_dates_from_range('2021-06-01', '2021-06-13')
    print(f"Date range for sessions generated, {len(result)}")
    assert True is True


def test_generate_game_score():
    user = generate_user()
    game = generate_game()
    game_session = generate_game_session(game, datetime.now())

    game_score = generate_game_score(user, game_session)
    print(f"Game score record generated successfully, {game}, {user.username}, {game_session}")
    assert True is True


def test_generate_user_with_data():
    user, game = generate_user_with_data('2021-06-01', '2021-06-13')
    print(f"User with data generated successfully, {user.username}, {game}")
    assert True is True
