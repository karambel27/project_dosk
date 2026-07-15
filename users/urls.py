from django.urls import path

from .views import ProfileUser

app_name = "users"

urlpatterns = [path("profile/", ProfileUser.as_view(), name="profile")]
