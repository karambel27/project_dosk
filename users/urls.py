from django.urls import path
from . import views
from .views import VerifyEmailView

app_name = 'users'

urlpatterns = [
    path("profile/", views.ProfileUser.as_view(), name='profile'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
]