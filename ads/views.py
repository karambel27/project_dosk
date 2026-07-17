from typing import Any

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django_filters.views import FilterView

from .filters import ResponseFilter
from .forms import AdsForm, ResponseForm
from .models import Ads, Category, Response


class IndexView(ListView):
    model = Ads
    template_name = "ads/index.html"
    context_object_name = "ads"
    extra_context = {"title": "MMORPG Board"}
    paginate_by = 3

    def get_queryset(self) -> QuerySet[Ads]:
        queryset = (
            Ads.objects.filter(is_published=True)
            .select_related("author", "category")
            .annotate(
                accepted_responses_count=Count(
                    "responses",
                    filter=Q(responses__is_accepted=Response.Status.ACCEPTED),
                )
            )
            .order_by("-created_at")
        )
        if category_id := self.request.GET.get("category"):
            queryset = queryset.filter(category_id=category_id)
        if search_query := self.request.GET.get("q", "").strip():
            queryset = queryset.filter(
                Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
                | Q(author__username__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.order_by("name")
        context["popcat"] = Category.objects.annotate(
            ads_count=Count("ads", filter=Q(ads__is_published=True))
        ).order_by("-ads_count", "name")[:5]
        context["active_ads_count"] = Ads.objects.filter(is_published=True).count()
        context["users_count"] = get_user_model().objects.count()
        return context


class ShowAdsView(DetailView):
    model = Ads
    template_name = "ads/showads.html"
    context_object_name = "ad"

    def get_queryset(self) -> QuerySet[Ads]:
        return Ads.objects.select_related("author", "category").annotate(
            responses_count=Count("responses")
        )

    def get_object(self, queryset: QuerySet[Ads] | None = None) -> Ads:
        advertisement = super().get_object(queryset)
        can_see_draft = self.request.user.is_authenticated and (
            advertisement.author_id == self.request.user.id or self.request.user.is_superuser
        )
        if not advertisement.is_published and not can_see_draft:
            raise Http404("Объявление не найдено.")
        return advertisement

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        accepted_responses = list(
            self.object.responses.filter(is_accepted=Response.Status.ACCEPTED)
            .select_related("author")
            .order_by("-created_at")
        )
        pending_responses = Response.objects.none()
        is_author = self.request.user.is_authenticated and self.request.user == self.object.author
        if self.request.user.is_authenticated:
            pending_responses = self.object.responses.filter(is_accepted=Response.Status.PENDING)
            if not is_author:
                pending_responses = pending_responses.filter(author=self.request.user)
            pending_responses = pending_responses.select_related("author")

        context.update(
            {
                "title": self.object.title,
                "responses": accepted_responses,
                "responses_expextation": pending_responses,
                "form": ResponseForm(),
                "count_responses": len(accepted_responses),
                "user_author": is_author,
            }
        )
        return context


class CreateAdsView(LoginRequiredMixin, CreateView):
    model = Ads
    template_name = "ads/ads_form.html"
    form_class = AdsForm
    extra_context = {"title": "Создание объявления"}

    def form_valid(self, form: AdsForm) -> HttpResponse:
        form.instance.author = self.request.user
        form.instance.is_published = "save_draft" not in self.request.POST
        return super().form_valid(form)


class UpdateAdsView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ads
    template_name = "ads/ads_form.html"
    fields = ["title", "content", "category", "is_published"]
    extra_context = {"title": "Редактирование объявления", "update": True}

    def test_func(self) -> bool:
        advertisement = self.get_object()
        return self.request.user == advertisement.author or self.request.user.is_superuser


class DeleteAdsView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Ads
    template_name = "ads/ads_delete.html"
    context_object_name = "post"
    extra_context = {"title": "Удаление объявления"}

    def get_success_url(self) -> str:
        return reverse("myads")

    def test_func(self) -> bool:
        advertisement = self.get_object()
        return self.request.user == advertisement.author or self.request.user.is_superuser


class CreateResponseView(LoginRequiredMixin, CreateView):
    model = Response
    form_class = ResponseForm

    def form_valid(self, form: ResponseForm) -> HttpResponse:
        advertisement = get_object_or_404(
            Ads.objects.select_related("author"),
            pk=self.kwargs["pk"],
            is_published=True,
        )
        if self.request.user == advertisement.author:
            raise PermissionDenied("Нельзя откликаться на собственное объявление.")
        if Response.objects.filter(author=self.request.user, ads=advertisement).exists():
            messages.error(self.request, "Вы уже откликались на это объявление.")
            return redirect("showads", pk=advertisement.pk)
        form.instance.author = self.request.user
        form.instance.ads = advertisement
        return super().form_valid(form)

    def form_invalid(self, form: ResponseForm) -> HttpResponse:
        messages.error(self.request, "Исправьте текст отклика и попробуйте снова.")
        return redirect("showads", pk=self.kwargs["pk"])

    def get_success_url(self) -> str:
        return reverse("showads", kwargs={"pk": self.kwargs["pk"]})


class ProfileShowView(DetailView):
    model = get_user_model()
    template_name = "ads/profile_show.html"
    context_object_name = "profile_user"
    extra_context = {"title": "Профиль автора"}

    def get_queryset(self) -> QuerySet:
        return (
            super()
            .get_queryset()
            .annotate(
                ads_count=Count("ads", distinct=True),
                responses_count=Count("responses", distinct=True),
            )
        )


class ResponsesMenuView(LoginRequiredMixin, TemplateView):
    template_name = "ads/responses_menu.html"
    extra_context = {"title": "Отклики"}


class ResponseAds(LoginRequiredMixin, FilterView):
    model = Response
    filterset_class = ResponseFilter
    template_name = "ads/responses_ads.html"
    context_object_name = "responses"
    extra_context = {"title": "Отклики на мои объявления"}
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Response]:
        return (
            Response.objects.filter(ads__author=self.request.user)
            .select_related("author", "ads")
            .order_by("-created_at")
        )

    def get_filterset_kwargs(self, filterset_class: type) -> dict[str, Any]:
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs["user"] = self.request.user
        return kwargs


class MyResponse(LoginRequiredMixin, ListView):
    model = Response
    template_name = "ads/my_response.html"
    context_object_name = "responses"
    extra_context = {"title": "Мои отклики"}
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Response]:
        return Response.objects.filter(author=self.request.user).select_related(
            "ads", "ads__author"
        )


@login_required
@require_POST
def update_response_status(
    request: HttpRequest,
    pk: int,
    target_status: int,
) -> HttpResponse:
    response = get_object_or_404(Response.objects.select_related("ads"), pk=pk)
    if request.user != response.ads.author and not request.user.is_superuser:
        raise PermissionDenied
    if response.is_accepted == Response.Status.PENDING:
        response.is_accepted = target_status
        response.save(update_fields=["is_accepted"])
    return redirect("myresponseads")


class MyAds(LoginRequiredMixin, ListView):
    model = Ads
    template_name = "ads/myads.html"
    context_object_name = "ads"
    extra_context = {"title": "Мои объявления"}
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Ads]:
        return (
            Ads.objects.filter(author=self.request.user)
            .select_related("author", "category")
            .annotate(responses_count=Count("responses"))
            .order_by("-created_at")
        )
