from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Account

class CustomUserAdmin(UserAdmin):
    model = Account
    ordering = ['email']
    list_display = ['email', 'is_staff', 'is_superuser']
    search_fields = ['email']
    readonly_fields = ('last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

admin.site.register(Account, CustomUserAdmin)
