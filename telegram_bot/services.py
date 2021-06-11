import requests


def send_statistic_to_tg_bot(chats_ids: list, message: str, token) -> None:
    """
    Service for sending statistic message to telegram specified chats.
    """
    for chat_id in chats_ids:
        requests.get(
            f'https://api.telegram.org/bot{token}/sendMessage',
            params={
                'chat_id': chat_id,
                'text': message
            },
        )
