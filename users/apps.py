from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = 'users'

    def ready(self):
        from .signals import friendship_post_save_signal_receiver
        from .signals import email_for_friendship_request_proccess
        from django.db.models.signals import post_save
        from .models import FriendshipRequest

        post_save.connect(
            friendship_post_save_signal_receiver,
            sender=FriendshipRequest,
            dispatch_uid='my_unique_identifier'
        )
        post_save.connect(
            email_for_friendship_request_proccess,
            sender=FriendshipRequest,
            dispatch_uid='my_unique_identifier2'
        )