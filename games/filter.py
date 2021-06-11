import django_filters

from games.models import Games
from users.models import CustomUser


class GameFilter(django_filters.FilterSet):

    name = django_filters.AllValuesFilter()
    user = django_filters.ModelChoiceFilter(
        field_name="sessions__scores__user",
        queryset=CustomUser.objects.prefetch_related("scores"),
        distinct=True
    )
    period = django_filters.DateFromToRangeFilter(
        field_name="sessions__created_at",
        label="Period of gaming",
        distinct=True,
        widget=django_filters.widgets.RangeWidget(attrs={'placeholder': 'e.g. 2021-04-03 (YYYY-MM-DD)'})
    )

    class Meta:
        model = Games
        fields = ['name']

    @property
    def qs(self):
        parent = super().qs
        return parent.prefetch_related("sessions", "sessions__scores", "sessions__scores__user")
