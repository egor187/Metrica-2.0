import datetime

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse_lazy


class CustomUser(AbstractUser):
    avatar = models.ImageField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)

    class Meta():
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name()

    def get_absolute_url(self):
        return '/users/'


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
