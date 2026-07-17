from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    photo = models.ImageField(
        upload_to="users/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name="Фотография",
    )
    birth_date = models.DateField(blank=True, null=True, verbose_name="Дата рождения")
    bio = models.TextField(blank=True, verbose_name="О себе")

    @property
    def is_email_verified(self) -> bool:
        return EmailAddress.objects.filter(user=self, verified=True).exists()
