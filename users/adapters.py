from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse


class MyAccountAdapter(DefaultAccountAdapter):

    def get_signup_redirect_url(self, request):
        return reverse('users:verify_email')