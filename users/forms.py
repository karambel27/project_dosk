import datetime

from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.mail import send_mail

from config import settings
from .models import EmailVerification
from .utils import generate_code


class ProfileUserForm(forms.ModelForm):
    username = forms.CharField(disabled=True, label='Логин', widget=forms.TextInput(attrs={'class': 'form-input'}))
    email = forms.CharField(disabled=True, label='E-mail', widget=forms.TextInput(attrs={'class': 'form-input'}))
    time_yeld = datetime.date.today().year
    data_bird = forms.DateField(widget=forms.SelectDateWidget(years=tuple(range(time_yeld - 80, time_yeld - 5))))

    class Meta:
        model = get_user_model()
        fields = ['photo', 'username', 'email', 'data_bird', "bio", 'first_name', 'last_name']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }


class MyCustomSignupForm(SignupForm):

    def save(self, request):
        user = super().save(request)
        # user.is_active = False
        # user.save(update_fields=['is_active'])
        # request.session['verify_user_id'] = user.id

        group_no_active = Group.objects.get(name='prava_no_active')
        user.groups.add(group_no_active)

        code = generate_code()

        EmailVerification.objects.update_or_create(user=user, defaults={'code': code})
        send_mail(
            'Подтверждение регистрации',
            f'Ваш код подтверждения: {code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        return user



class VerifyCodeForm(forms.Form):
    code = forms.CharField(max_length=6,min_length=6,label='',widget=forms.TextInput(
            attrs={
                'placeholder': '123456'
            }
        )
    )