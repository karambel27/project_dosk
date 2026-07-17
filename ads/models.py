from typing import Any

import bleach
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.html import strip_tags

ALLOWED_CONTENT_TAGS = {
    "a",
    "blockquote",
    "br",
    "em",
    "h2",
    "h3",
    "img",
    "li",
    "ol",
    "p",
    "s",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
}
ALLOWED_CONTENT_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
}


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Категория")
    ico = models.ImageField(upload_to="cat_ico", blank=True, null=True, verbose_name="Иконка")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Ads(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="ads",
    )
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержимое объявления")
    is_published = models.BooleanField(default=False, verbose_name="Опубликовано")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        verbose_name="Категория",
        related_name="ads",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        ordering = ["-created_at"]

    def get_absolute_url(self) -> str:
        return reverse("showads", kwargs={"pk": self.pk})

    def __str__(self) -> str:
        return self.title

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.title = self.title.strip()
        self.title = self.title[:1].upper() + self.title[1:]
        self.content = bleach.clean(
            self.content,
            tags=ALLOWED_CONTENT_TAGS,
            attributes=ALLOWED_CONTENT_ATTRIBUTES,
            protocols={"http", "https", "mailto"},
            strip=True,
        )
        super().save(*args, **kwargs)

    def preview(self) -> str:
        plain_text = strip_tags(self.content).replace("&nbsp;", " ").strip()
        suffix = "..." if len(plain_text) > 75 else ""
        return f"{plain_text[:75]}{suffix}"


class Response(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 0, "Ожидает ответа"
        REJECTED = 1, "Отклонён"
        ACCEPTED = 2, "Принят"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Автор",
        related_name="responses",
    )
    ads = models.ForeignKey(
        Ads,
        on_delete=models.CASCADE,
        verbose_name="Объявление",
        related_name="responses",
    )
    text = models.TextField(verbose_name="Текст отклика")
    is_accepted = models.PositiveSmallIntegerField(
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Отклик"
        verbose_name_plural = "Отклики"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["author", "ads"],
                name="unique_response_per_author_and_ad",
            )
        ]

    def __str__(self) -> str:
        return f"Отклик от {self.author} на {self.ads}"
