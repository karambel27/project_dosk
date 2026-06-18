from django.contrib.auth.models import AbstractUser
from django.db import models
from allauth.account.models import EmailAddress

from config import settings


class User(AbstractUser):
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True, null=True,
                              verbose_name='Фотография')
    data_bird = models.DateTimeField(blank=True, null=True, verbose_name="Дата рождения")

    bio = models.TextField(blank=True, verbose_name='О себе')

    @property
    def is_email_verified(self):
        return EmailAddress.objects.filter(
            user=self,
            verified=True
        ).exists()



class EmailVerification(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.code}'