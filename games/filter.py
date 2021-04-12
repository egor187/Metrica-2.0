import django_filters

from games.models import Games
from users.models import CustomUser


# class SessionFilter(django_filters.FilterSet):
#     game = django_filters.ModelChoiceFilter(queryset=Games.objects.all())
#
#     created_at = django_filters.NumberFilter(
#         label='month played game',
#         method='get_month',
#     )
#     user = django_filters.ModelChoiceFilter(
#         queryset=CustomUser.objects.prefetch_related("scores"),
#         field_name="scores__user",
#         label="User"
#     )
#
#     period = django_filters.DateFromToRangeFilter(
#         field_name="created_at",
#         label="Period of gaming",
#         widget=django_filters.widgets.RangeWidget(attrs={'placeholder': 'e.g. 2021-04-03 (YYYY-MM-DD)'})
#     )
#
#     class Meta:
#         model = GameSession
#         fields = ["name", "created_at", ]
#
#     def get_month(self, queryset, field_name, month):
#         return queryset.filter(created_at__month=month)
#
#     def get_user(self, queryset, field_name, user):
#         return queryset.filter(scores__user=user)
#
#     @property
#     def qs(self):
#         parent = super().qs
#         return parent.prefetch_related("game", "scores__user")


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
