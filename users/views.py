from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from .forms import ProfileUserForm


class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = "users/profile.html"
    extra_context = {"title": "Профиль"}

    def get_success_url(self) -> str:
        return reverse_lazy("users:profile")

    def get_object(self, queryset: QuerySet | None = None) -> Any:
        return self.request.user
