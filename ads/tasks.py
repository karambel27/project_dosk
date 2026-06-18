from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from .models import Ads, Category


@shared_task
def send_weekly_digest():
    week_ago = timezone.now() - timedelta(days=7)

    new_ads = Ads.objects.filter(
        is_published=True,
        created_at__gte=week_ago
    ).order_by('-created_at')[:5]

    users = get_user_model().objects.filter(
        emailaddress__verified=True,
        is_active=True,
        email__isnull=False
    ).exclude(email='')

    if not new_ads.exists():
        return 'Новых объявлений нет'

    ads_text = ''

    for ad in new_ads:
        ads_text += f'- {ad.title}\n'

    for user in users:
        message = (
            f'Здравствуйте, {user.username}!\n\n'
            f'Итоги недели на MMORPG Board.\n\n'
            f'Новых объявлений за неделю: {new_ads.count()}\n\n'
            f'Свежие объявления:\n'
            f'{ads_text}\n'
            f'Перейдите на сайт, чтобы посмотреть подробности.'
        )

        send_mail(
            subject='Итоги недели на MMORPG Board',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

    return f'Рассылка отправлена: {users.count()} пользователей'