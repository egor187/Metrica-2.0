import django_filters


class FriendshipRequestFilter(django_filters.FilterSet):
    is_accepted = django_filters.BooleanFilter(
        lookup_expr='exact',
        label='принятые запросы',
        field_name='is_accepted',
    )

    is_rejected = django_filters.BooleanFilter(
        lookup_expr='isnull',
        label='нерассмотренные запросы',
        field_name='is_accepted',
    )
