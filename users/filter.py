import django_filters


class FriendshipRequestFilter(django_filters.FilterSet):
    """
    Filter friendship requests depends on is request accepted or rejected by requested user
    """
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
