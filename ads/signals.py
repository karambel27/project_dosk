from functools import partial
from typing import Any

from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Response
from .tasks import send_new_response_notification, send_response_status_notification


@receiver(pre_save, sender=Response)
def remember_old_response_status(
    sender: type[Response],
    instance: Response,
    **kwargs: Any,
) -> None:
    if not instance.pk:
        instance._old_is_accepted = None
        return
    instance._old_is_accepted = (
        Response.objects.filter(pk=instance.pk).values_list("is_accepted", flat=True).first()
    )


@receiver(post_save, sender=Response)
def enqueue_response_notification(
    sender: type[Response],
    instance: Response,
    created: bool,
    **kwargs: Any,
) -> None:
    if created:
        transaction.on_commit(
            partial(send_new_response_notification.delay, instance.pk),
            robust=True,
        )
        return

    old_status = getattr(instance, "_old_is_accepted", None)
    status_changed = old_status != instance.is_accepted
    should_notify = instance.is_accepted in {
        Response.Status.ACCEPTED,
        Response.Status.REJECTED,
    }
    if status_changed and should_notify:
        transaction.on_commit(
            partial(send_response_status_notification.delay, instance.pk),
            robust=True,
        )
