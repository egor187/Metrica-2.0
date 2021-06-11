from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django_summernote.admin import SummernoteModelAdmin

from users.forms import CustomUserCreationForm, CustomUserUpdateForm
from .models import CustomUser, ClaimTopic, Claim


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserUpdateForm
    model = CustomUser
    list_display = (
        'username', 'email', 'is_staff', 'is_active', 'first_name', 'last_name', 'avatar', 'friendship_repr'
    )
    list_filter = ('username', 'is_staff', 'is_active',)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('avatar',)}),
        (None, {'fields': ('friendship',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('avatar',)}),
        (None, {'fields': ('friendship',)}),
    )

    search_fields = ('username',)
    ordering = ('username',)


class ClaimAdmin(SummernoteModelAdmin):
    summernote_fields = '__all__'


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Claim, ClaimAdmin)
admin.site.register(ClaimTopic)
