from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from django.conf import settings
from django.urls import reverse
from django.utils.html import strip_tags


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name='Категория')
    ico = models.ImageField(upload_to='cat_ico', blank=True, null=True,
                              verbose_name='Иконки')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']


class Ads(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Автор', related_name='ads')
    title = models.CharField(max_length=255, verbose_name='Заголовок')
    content = RichTextUploadingField(verbose_name='Содержимое объявления')
    is_published = models.BooleanField(default=False, verbose_name='Опубликовано')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='Категория', related_name='ads')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата Создания')
    updated_at = models.DateTimeField(auto_now=True,verbose_name='Дата обновления')

    def get_absolute_url(self):
        return reverse( 'showads' , kwargs={'pk': self.pk})

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.title = self.title.strip()
        self.title = self.title[:1].upper() + self.title[1:]
        super().save(*args, **kwargs)

    def preview(self):
        return f"{strip_tags(self.content).replace('&nbsp;', ' ')[:75]}..."

    @property
    def published_responses_count(self):
        return self.responses.filter(is_accepted=2).count()

    class Meta:
        verbose_name = 'Объявление'
        verbose_name_plural = 'Объявления'
        ordering = ['created_at']


class Response(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Автор', related_name='responses')
    ads = models.ForeignKey(Ads, on_delete=models.CASCADE, verbose_name='Объявление', related_name='responses')
    text = models.TextField(verbose_name='Текст отклика')
    is_accepted = models.IntegerField(default=0, verbose_name='Принят')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    def __str__(self):
        return f'Отклик от {self.author} на {self.ads}'



    class Meta:
        verbose_name = 'Отклик'
        verbose_name_plural = 'Отклики'
        ordering = ['-created_at']


