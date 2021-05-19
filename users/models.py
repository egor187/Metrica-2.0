import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib import admin
from django.db.models import Q
from django.urls import reverse_lazy


class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)
    friendship = models.ManyToManyField('self', verbose_name='Друзья', blank=True, symmetrical=False)

    @admin.display
    def friendship_repr(self):
        return list(self.friendship.values_list('username', flat=True))

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name()

    def get_absolute_url(self):
        return reverse_lazy('users:users_detail', args=[self.pk])


class FriendshipRequest(models.Model):
    from_user = models.ForeignKey(
        CustomUser,
        verbose_name='Отправитель запроса',
        on_delete=models.CASCADE,
        related_name='friendship_request_sent'
    )
    to_user = models.ForeignKey(
        CustomUser,
        verbose_name='Получатель запроса',
        on_delete=models.CASCADE,
        related_name='friendship_request_received'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания запроса'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата ответа запроса'
    )
    message = models.CharField(
        max_length=100,
        verbose_name='Сообщение к запросу на добавление в друзья',
        null=True,
        blank=True
    )
    is_rejected = models.BooleanField(
        verbose_name='Отклоненный запрос',
        blank=True,
        null=True
    )
    is_accepted = models.BooleanField(
        verbose_name='Принятый запрос',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "Friendship Request"
        verbose_name_plural = "Friendship Requests"
        unique_together = ("from_user", "to_user", "is_rejected", "is_accepted")
        constraints = [
            models.CheckConstraint(
                name='status_unique',
                check=Q(is_rejected=True) & Q(is_accepted=False) | Q(is_rejected=False) & Q(is_accepted=True)
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Friendship request from {self.from_user.username} " \
               f"to {self.to_user.username} created at {self.created_at}"


class ClaimTopic(models.Model):
    CHOICES = [
        ('adding a game', 'adding a game'),
        ('error in statistics', 'error in statistics'),
        ('wishes', 'wishes'),
        ('general issues', 'general issues'),
    ]
    name = models.CharField(max_length=25, choices=CHOICES)

    def __str__(self):
        return self.name


class Claim(models.Model):
    topic = models.ForeignKey(ClaimTopic, on_delete=models.SET_NULL, null=True, related_name='claims')
    claim = models.TextField('text of the claim')
    claimer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='claims')
    created_at = models.DateTimeField(auto_now_add=True)
    answer_date_expiration = models.DateTimeField(null=True)

    def __str__(self):
        return self.claim

    def get_absolute_url(self):
        return reverse_lazy('users:users_index')

    def save(self, *args, **kwargs):
        """
        Override super() method to get opportunity to use F() expression in model field creation (deltatime)
        for "answer_date_expiration" field
        :param args:
        :param kwargs:
        :return:
        """
        # NOT covered in tests
        super().save(*args, **kwargs)
        self.answer_date_expiration = models.F('created_at') + datetime.timedelta(days=14)
        super().save(*args, **kwargs)

        # KISS and covered in tests
        # self.answer_date_expiration = datetime.datetime.now() + datetime.timedelta(days=14)
        # super().save(*args, **kwargs)
