from django.core.mail import send_mail


def friendship_post_save_signal_receiver(sender, **kwargs):
    print('"post_save" signal working correct!')


def email_for_friendship_request_process(sender, **kwargs):
    """
    Sends email to user who received the friend request on 'post_save' signal
    """
    subject = 'Friendship request'
    message = f"{kwargs.get('instance').from_user} is ask you for friend. You may answer on site"
    recipient_email = [
        kwargs.get('instance').to_user.email,
    ]
    send_mail(
        subject=subject,
        message=message,
        from_email=None,
        recipient_list=recipient_email
    )
