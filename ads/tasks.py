from datetime import timedelta
from smtplib import SMTPException

from allauth.account.models import EmailAddress
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from .models import Ads, Response

RETRYABLE_EMAIL_ERRORS = (SMTPException, OSError)


@shared_task(
    autoretry_for=RETRYABLE_EMAIL_ERRORS,
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_new_response_notification(response_id: int) -> str:
    try:
        response = Response.objects.select_related("ads__author", "author").get(pk=response_id)
    except Response.DoesNotExist:
        return "response no longer exists"

    recipient = response.ads.author
    if (
        not recipient.email
        or not EmailAddress.objects.filter(user=recipient, verified=True).exists()
    ):
        return "recipient has no verified email"

    send_mail(
        subject="Новый отклик на ваше объявление",
        message=(
            f"Здравствуйте, {recipient.username}!\n\n"
            f"На объявление «{response.ads.title}» оставлен новый отклик.\n\n"
            f"Автор: {response.author.username}\n"
            f"Текст: {response.text}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient.email],
    )
    return "notification sent"


@shared_task(
    autoretry_for=RETRYABLE_EMAIL_ERRORS,
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_response_status_notification(response_id: int) -> str:
    try:
        response = Response.objects.select_related("ads", "author").get(pk=response_id)
    except Response.DoesNotExist:
        return "response no longer exists"

    if response.is_accepted not in {Response.Status.ACCEPTED, Response.Status.REJECTED}:
        return "status does not require notification"
    if (
        not response.author.email
        or not EmailAddress.objects.filter(
            user=response.author,
            verified=True,
        ).exists()
    ):
        return "recipient has no verified email"

    status_text = response.get_is_accepted_display().lower()
    send_mail(
        subject=f"Ваш отклик {status_text}",
        message=(
            f"Здравствуйте, {response.author.username}!\n\n"
            f"Ваш отклик на объявление «{response.ads.title}» {status_text}.\n\n"
            f"Текст: {response.text}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[response.author.email],
    )
    return "notification sent"


@shared_task
def send_weekly_digest() -> str:
    week_ago = timezone.now() - timedelta(days=7)
    advertisements = list(
        Ads.objects.filter(is_published=True, created_at__gte=week_ago)
        .order_by("-created_at")
        .values_list("id", flat=True)[:5]
    )
    if not advertisements:
        return "no new advertisements"

    user_ids = (
        get_user_model()
        .objects.filter(emailaddress__verified=True, is_active=True)
        .exclude(email="")
        .values_list("id", flat=True)
        .distinct()
    )
    sent = 0
    for user_id in user_ids.iterator():
        send_digest_email.delay(user_id, advertisements)
        sent += 1
    return f"scheduled digests: {sent}"


@shared_task(
    autoretry_for=RETRYABLE_EMAIL_ERRORS,
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_digest_email(user_id: int, advertisement_ids: list[int]) -> str:
    user = get_user_model().objects.filter(pk=user_id, is_active=True).first()
    if user is None or not user.email:
        return "recipient unavailable"

    advertisements = list(
        Ads.objects.filter(pk__in=advertisement_ids, is_published=True).order_by("-created_at")
    )
    if not advertisements:
        return "advertisements unavailable"

    ads_text = "\n".join(f"- {advertisement.title}" for advertisement in advertisements)
    send_mail(
        subject="Итоги недели на MMORPG Board",
        message=(f"Здравствуйте, {user.username}!\n\nСвежие объявления за неделю:\n{ads_text}"),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    return "digest sent"
