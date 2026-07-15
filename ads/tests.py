from unittest.mock import patch

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core import mail
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import Ads, Category, Response
from .tasks import send_new_response_notification, send_response_status_notification


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"],
)
class BoardTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.owner = user_model.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="strong-test-password",
        )
        self.responder = user_model.objects.create_user(
            username="responder",
            email="responder@example.com",
            password="strong-test-password",
        )
        self.outsider = user_model.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="strong-test-password",
        )
        self.category = Category.objects.create(name="Гильдии")
        self.advertisement = Ads.objects.create(
            author=self.owner,
            category=self.category,
            title="поиск группы",
            content="Нужна группа для рейда",
            is_published=True,
        )
        self.draft = Ads.objects.create(
            author=self.owner,
            category=self.category,
            title="черновик",
            content="Скрытый текст",
            is_published=False,
        )

    def test_index_hides_drafts_supports_search_and_avoids_n_plus_one(self) -> None:
        Response.objects.create(
            author=self.responder,
            ads=self.advertisement,
            text="Готов участвовать",
            is_accepted=Response.Status.ACCEPTED,
        )
        with CaptureQueriesContext(connection) as first_queries:
            first_response = self.client.get(reverse("home"), {"q": "группы"})

        for index in range(4):
            Ads.objects.create(
                author=self.owner,
                category=self.category,
                title=f"Группа {index}",
                content="Описание",
                is_published=True,
            )
        with CaptureQueriesContext(connection) as many_queries:
            self.client.get(reverse("home"), {"q": "групп"})

        self.assertEqual(first_response.status_code, 200)
        self.assertContains(first_response, "Поиск группы")
        self.assertNotContains(first_response, "Черновик")
        self.assertEqual(len(many_queries), len(first_queries))
        self.assertEqual(first_response.context["ads"][0].accepted_responses_count, 1)

    def test_draft_is_visible_only_to_its_owner(self) -> None:
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 404)

        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 200)

        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 404)

    def test_authenticated_user_can_create_advertisement(self) -> None:
        self.client.force_login(self.responder)
        response = self.client.post(
            reverse("createdads"),
            {"title": "новое объявление", "content": "Текст", "category": self.category.pk},
        )

        self.assertEqual(response.status_code, 302)
        created = Ads.objects.get(author=self.responder)
        self.assertEqual(created.title, "Новое объявление")
        self.assertTrue(created.is_published)

    def test_owner_can_update_but_outsider_cannot(self) -> None:
        payload = {
            "title": "обновлённое объявление",
            "content": "Новый текст",
            "category": self.category.pk,
            "is_published": True,
        }
        self.client.force_login(self.outsider)
        self.assertEqual(
            self.client.post(
                reverse("updatedads", args=[self.advertisement.pk]), payload
            ).status_code,
            403,
        )

        self.client.force_login(self.owner)
        response = self.client.post(reverse("updatedads", args=[self.advertisement.pk]), payload)
        self.assertEqual(response.status_code, 302)
        self.advertisement.refresh_from_db()
        self.assertEqual(self.advertisement.title, "Обновлённое объявление")

    def test_author_cannot_respond_to_own_advertisement(self) -> None:
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("create_response", args=[self.advertisement.pk]),
            {"text": "Собственный отклик"},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Response.objects.count(), 0)

    def test_user_can_respond_only_once(self) -> None:
        self.client.force_login(self.responder)
        url = reverse("create_response", args=[self.advertisement.pk])

        self.assertEqual(self.client.post(url, {"text": "Первый отклик"}).status_code, 302)
        self.assertEqual(self.client.post(url, {"text": "Повторный отклик"}).status_code, 302)
        self.assertEqual(Response.objects.count(), 1)

    def test_response_status_requires_post_and_ad_owner(self) -> None:
        response_object = Response.objects.create(
            author=self.responder,
            ads=self.advertisement,
            text="Отклик",
        )
        url = reverse("accept", args=[response_object.pk])

        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 405)
        response_object.refresh_from_db()
        self.assertEqual(response_object.is_accepted, Response.Status.PENDING)

        self.client.force_login(self.outsider)
        self.assertEqual(self.client.post(url).status_code, 403)

        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(url).status_code, 302)
        response_object.refresh_from_db()
        self.assertEqual(response_object.is_accepted, Response.Status.ACCEPTED)

    def test_received_responses_are_scoped_and_eager_loaded(self) -> None:
        Response.objects.create(author=self.responder, ads=self.advertisement, text="Отклик")
        other_ad = Ads.objects.create(
            author=self.outsider,
            category=self.category,
            title="Чужое объявление",
            content="Текст",
            is_published=True,
        )
        Response.objects.create(author=self.owner, ads=other_ad, text="Чужой отклик")
        self.client.force_login(self.owner)

        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse("myresponseads"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["responses"]), list(self.advertisement.responses.all())
        )
        self.assertLessEqual(len(queries), 6)

    def test_rich_text_is_sanitized_before_saving(self) -> None:
        unsafe_advertisement = Ads.objects.create(
            author=self.owner,
            category=self.category,
            title="безопасный html",
            content='<p>Текст</p><script>alert(1)</script><a href="javascript:alert(1)">link</a>',
            is_published=True,
        )

        self.assertNotIn("<script", unsafe_advertisement.content)
        self.assertNotIn("javascript:", unsafe_advertisement.content)
        self.assertIn("<p>Текст</p>", unsafe_advertisement.content)

    def test_response_signal_schedules_background_notification(self) -> None:
        with patch("ads.signals.send_new_response_notification.delay") as task_delay:
            with self.captureOnCommitCallbacks(execute=True):
                response = Response.objects.create(
                    author=self.responder,
                    ads=self.advertisement,
                    text="Отклик",
                )

        task_delay.assert_called_once_with(response.pk)

    def test_notification_tasks_send_mail_only_to_verified_addresses(self) -> None:
        EmailAddress.objects.create(
            user=self.owner,
            email=self.owner.email,
            verified=True,
            primary=True,
        )
        EmailAddress.objects.create(
            user=self.responder,
            email=self.responder.email,
            verified=True,
            primary=True,
        )
        response = Response.objects.create(
            author=self.responder,
            ads=self.advertisement,
            text="Отклик",
        )

        send_new_response_notification(response.pk)
        response.is_accepted = Response.Status.ACCEPTED
        response.save(update_fields=["is_accepted"])
        send_response_status_notification(response.pk)

        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to, [self.owner.email])
        self.assertEqual(mail.outbox[1].to, [self.responder.email])
