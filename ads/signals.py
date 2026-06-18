from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Response


@receiver(post_save, sender=Response)
def send_response_email_to_ad_author(sender, instance, created, **kwargs):
    if not created:
        return

    ad = instance.ads
    ad_author = ad.author
    response_author = instance.author
    message = (
        f'Здравствуйте, {ad_author.username}!\n\n'
        f'На ваше объявление "{ad.title}" оставили новый отклик.\n\n'
        f'Автор отклика: {response_author.username}\n\n'
        f'Текст отклика:\n{instance.text}\n\n'
        f'Перейдите на сайт, чтобы посмотреть отклик.'
    )

    # print(message)

    send_mail(
        subject='Новый отклик на ваше объявление',
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[ad_author.email],
        fail_silently=False,
    )


@receiver(pre_save, sender=Response)
def remember_old_response_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_is_accepted = None
        return

    try:
        old_response = Response.objects.get(pk=instance.pk)
        instance._old_is_accepted = old_response.is_accepted
    except Response.DoesNotExist:
        instance._old_is_accepted = None


@receiver(post_save, sender=Response)
def send_email_when_response_status_changed(sender, instance, created, **kwargs):
    if created:
        return

    old_status = getattr(instance, '_old_is_accepted', None)

    if old_status == instance.is_accepted:
        return

    if not instance.author.email:
        return

    if instance.is_accepted == 1:
        status_text = 'отклонён'
        subject = 'Ваш отклик отклонили'

    elif instance.is_accepted == 2:
        status_text = 'принят'
        subject = 'Ваш отклик приняли'

    else:
        return

    email = EmailAddress.objects.get(user=instance.author)
    if email.verified:
        send_mail(
            subject=subject,
            message=(
                f'Здравствуйте, {instance.author.username}!\n\n'
                f'Ваш отклик на объявление "{instance.ads.title}" был {status_text}.\n\n'
                f'Текст вашего отклика:\n'
                f'{instance.text}\n\n'
                f'Перейдите на сайт, чтобы посмотреть подробности.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.author.email],
            fail_silently=False,
        )
