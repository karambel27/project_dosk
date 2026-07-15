from allauth.account.models import EmailAddress
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(PASSWORD_HASHERS=["django.contrib.auth.hashers.MD5PasswordHasher"])
class UserProfileTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="profile-user",
            email="profile@example.com",
            password="strong-test-password",
        )

    def test_profile_requires_login_and_edits_only_current_user(self) -> None:
        url = reverse("users:profile")
        self.assertEqual(self.client.get(url).status_code, 302)

        self.client.force_login(self.user)
        response = self.client.post(
            url,
            {
                "username": self.user.username,
                "email": self.user.email,
                "first_name": "Иван",
                "last_name": "Иванов",
                "bio": "Игрок",
                "birth_date": "2000-01-02",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Иван")
        self.assertEqual(str(self.user.birth_date), "2000-01-02")

    def test_email_verification_uses_allauth_mandatory_flow(self) -> None:
        self.assertEqual(settings.ACCOUNT_EMAIL_VERIFICATION, "mandatory")
        self.assertFalse(self.user.is_email_verified)

        EmailAddress.objects.create(
            user=self.user,
            email=self.user.email,
            verified=True,
            primary=True,
        )
        self.assertTrue(self.user.is_email_verified)
