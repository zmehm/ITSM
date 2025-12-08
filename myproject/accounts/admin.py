# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'date_of_birth', 'is_staff', 'is_active']
    
    # Add 'date_of_birth' to the edit user form
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('date_of_birth',)}),  # Add 'date_of_birth' to the edit form
    )
    
    # Add 'date_of_birth' to the add user form
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('date_of_birth',)}),  # Add 'date_of_birth' to the add user form
    )

# Register CustomUserAdmin to the admin site
admin.site.register(CustomUser, CustomUserAdmin)
