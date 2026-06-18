from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import UpdateView, FormView
from users.forms import ProfileUserForm, VerifyCodeForm
from users.models import EmailVerification
from allauth.account.models import EmailAddress
from django.contrib.auth.models import Group


class ProfileUser(LoginRequiredMixin, UpdateView):
    model = get_user_model()
    form_class = ProfileUserForm
    template_name = 'users/profile.html'
    extra_context = {'title': 'Профиль'}

    def get_success_url(self):
        return reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user


class VerifyEmailView(FormView):
    template_name = 'users/verify_email.html'
    form_class = VerifyCodeForm
    success_url = '/'

    # def dispatch(self, request, *args, **kwargs):
    #     if not request.session.get('verify_user_id'):
    #         return redirect('account_signup')

        # return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # user_id = self.request.session.get('verify_user_id')

        # try:
        #     user = get_user_model().objects.get(pk=user_id)
        # except get_user_model().DoesNotExist:
        #     form.add_error(None, 'Пользователь не найден. Зарегистрируйтесь заново.')
        #     return self.form_invalid(form)
        #
        # try:
        #     obj = EmailVerification.objects.get(user=user)
        # except EmailVerification.DoesNotExist:
        #     form.add_error(None, 'Код подтверждения не найден.')
        #     return self.form_invalid(form)

        user = self.request.user
        obj = EmailVerification.objects.get(user=user)


        if obj.code == form.cleaned_data['code']:
            obj.delete()

            group_active = Group.objects.get(name='prava_active')
            user.groups.add(group_active)

            email = EmailAddress.objects.get(user=user)
            email.verified = True
            email.primary = True
            email.save(update_fields=['verified', 'primary'])
            # self.request.session.pop('verify_user_id', None)

            return super().form_valid(form)

        form.add_error('code', 'Неверный код')
        return self.form_invalid(form)
