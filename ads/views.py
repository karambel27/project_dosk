from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django_filters.views import FilterView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin, UserPassesTestMixin

from ads.filters import ResponseFilter
from ads.forms import Formaddads, ResponseForm
from ads.models import Ads, Category, Response


class IndexView(ListView):
    model = Ads
    template_name = 'ads/index.html'
    ordering = '-created_at'
    context_object_name = 'ads'
    extra_context = {
        'title': 'MMORPG Board'}
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.order_by('name')
        context['popcat'] = Category.objects.annotate(ads_count=Count
        ('ads', filter=Q(ads__is_published=True))).order_by('-ads_count')[:5]
        context['active_ads_count'] = Ads.objects.filter(is_published=True).count()
        context['users_count'] = get_user_model().objects.count()
        return context

    def get_queryset(self):
        queryset = Ads.objects.filter(is_published=True).order_by('-created_at')
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


class ShowAdsView(DetailView):
    model = Ads
    template_name = 'ads/showads.html'
    context_object_name = 'ad'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.get_object().title
        context['responses'] = self.object.responses.filter(is_accepted=2).order_by('-created_at')
        context['form'] = ResponseForm()
        context['count_responses'] = context['responses'].count()
        context['user_author'] = self.request.user == self.object.author
        if self.request.user.is_authenticated:
            context['responses_expextation'] = self.object.responses.filter(is_accepted=0, author=self.request.user)
        if self.request.user.is_authenticated and self.request.user == self.object.author:
            context['responses_expextation'] = self.object.responses.filter(is_accepted=0)

        return context

    def get_object(self, queryset=None):
        obj = super().get_object()
        if obj.author == self.request.user:
            return Ads.objects.get(pk=self.kwargs['pk'])
        return get_object_or_404(Ads.objects.filter(is_published=True), pk=self.kwargs.get('pk'))


class CreateAdsView(PermissionRequiredMixin, CreateView):
    model = Ads
    template_name = 'ads/ads_form.html'
    form_class = Formaddads
    extra_context = {'title': 'Создание объявления'}
    permission_required = 'ads.add_ads'

    def form_valid(self, form):
        form.instance.author = self.request.user

        form.instance.is_published = 'save_draft' not in self.request.POST

        return super().form_valid(form)


class UpdateAdsView(UserPassesTestMixin, UpdateView):
    model = Ads
    template_name = 'ads/ads_form.html'
    fields = ['title', 'content', 'category', 'is_published']
    extra_context = {'title': 'Редактирование объявления', 'update': True}

    def test_func(self):
        ads = self.get_object()
        return self.request.user == ads.author or self.request.user.is_superuser


class DeleteAdsView(UserPassesTestMixin, DeleteView):
    model = Ads
    template_name = 'ads/ads_delete.html'
    context_object_name = 'post'
    extra_context = {'title': 'Удаление объяления'}

    def get_success_url(self):
        return reverse('myads')

    def test_func(self):
        ads = self.get_object()
        return self.request.user == ads.author or self.request.user.is_superuser


class CreateResponseView(LoginRequiredMixin, CreateView):
    model = Response
    form_class = ResponseForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.ads = get_object_or_404(Ads, pk=self.kwargs['pk'])
        if self.request.user == form.instance.ads.author:
            pass
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('showads', kwargs={'pk': self.kwargs['pk']})


class ProfileShowView(DetailView):
    model = get_user_model()
    template_name = 'ads/profile_show.html'
    context_object_name = 'profile_user'
    extra_context = {'title': 'Профиль автора'}


class ResponsesMenuView(PermissionRequiredMixin, TemplateView):
    template_name = 'ads/responses_menu.html'
    extra_context = {'title': 'Отклики'}
    permission_required = 'ads.add_response'


class ResponseAds(PermissionRequiredMixin, FilterView):
    model = Response
    filterset_class = ResponseFilter
    template_name = 'ads/responses_ads.html'
    context_object_name = 'responses'
    extra_context = {'title': 'Отклики на мои объявления'}
    permission_required = 'ads.add_ads'

    def get_queryset(self):
        return Response.objects.filter(
            ads__author=self.request.user).order_by('-created_at')

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['user'] = self.request.user
        return kwargs


class MyResponse(PermissionRequiredMixin, ListView):
    model = Response
    template_name = 'ads/my_response.html'
    ordering = '-created_at'
    context_object_name = 'responses'
    extra_context = {'title': 'Мои отклики'}
    permission_required = 'ads.add_response'

    def get_queryset(self):
        return Response.objects.filter(author=self.request.user)


def acceptres(request, pk):
    response = get_object_or_404(Response, pk=pk)

    if request.user != response.ads.author and not request.user.is_superuser:
        raise PermissionDenied

    response.is_accepted = 2
    response.save()

    return redirect(request.META.get('HTTP_REFERER'))


def deleteres(request, pk):
    response = get_object_or_404(Response, pk=pk)

    if request.user != response.ads.author and not request.user.is_superuser:
        raise PermissionDenied

    response.is_accepted = 1
    response.save()

    return redirect(request.META.get('HTTP_REFERER'))


class MyAds(PermissionRequiredMixin, ListView):
    model = Ads
    template_name = 'ads/myads.html'
    ordering = '-created_at'
    context_object_name = 'ads'
    extra_context = {
        'title': 'Мои объявления'}
    permission_required = 'ads.add_ads'

    def get_queryset(self):
        return Ads.objects.filter(author=self.request.user)
