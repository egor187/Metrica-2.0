from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.forms import CustomUserCreationForm, CustomUserUpdateForm
from .models import CustomUser, ClaimTopic, Claim


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserUpdateForm
    model = CustomUser
    list_display = ('username', 'email', 'is_staff', 'is_active', 'first_name', 'last_name', 'avatar')
    list_filter = ('username', 'is_staff', 'is_active',)
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('avatar',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('avatar',)}),
    )

    search_fields = ('username',)
    ordering = ('username',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Claim)
admin.site.register(ClaimTopic)
