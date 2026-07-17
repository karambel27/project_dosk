import django_filters

from .models import Ads, Response


class ResponseFilter(django_filters.FilterSet):
    ads = django_filters.ModelChoiceFilter(
        queryset=Ads.objects.none(),
        label="Объявление",
        empty_label="Все объявления",
    )

    class Meta:
        model = Response
        fields = ["ads"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.filters["ads"].queryset = Ads.objects.filter(author=user).order_by("-created_at")
