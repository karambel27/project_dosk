from datetime import date

from django import forms
from django.contrib.auth import get_user_model


class ProfileUserForm(forms.ModelForm):
    username = forms.CharField(
        disabled=True,
        label="Логин",
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    email = forms.EmailField(
        disabled=True,
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "form-input"}),
    )
    birth_date = forms.DateField(
        required=False,
        label="Дата рождения",
        widget=forms.SelectDateWidget(years=range(date.today().year - 80, date.today().year - 5)),
    )

    class Meta:
        model = get_user_model()
        fields = ["photo", "username", "email", "birth_date", "bio", "first_name", "last_name"]
        labels = {"first_name": "Имя", "last_name": "Фамилия"}
