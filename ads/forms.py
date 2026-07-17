from django import forms

from .models import Ads, Category, Response


class AdsForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Категория не выбрана",
        label="Категория",
    )

    class Meta:
        model = Ads
        fields = ["title", "content", "category"]


class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(
                attrs={
                    "placeholder": "Напишите ваш отклик...",
                    "class": "response-textarea",
                    "rows": 4,
                }
            )
        }

    def clean_text(self) -> str:
        text = self.cleaned_data["text"].strip()
        if len(text) < 2:
            raise forms.ValidationError("Отклик должен содержать не менее двух символов.")
        return text
