# accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Employee, Category, SubCategory, Incident 

# --- 1. CustomUser Admin Setup (Your Existing Code) ---
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'is_staff', 'is_active']
    
    # Add 'phone_number', 'address', and 'date_of_birth' to the edit user form
    fieldsets = UserAdmin.fieldsets + (
        ('Contact Info & Birthdate', {'fields': ('phone_number', 'address', 'date_of_birth',)}), 
    )
    
    # Add fields to the add user form
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('phone_number', 'address', 'date_of_birth',)}),
    )

admin.site.register(CustomUser, CustomUserAdmin)


# --- 2. Employee Admin Setup ---
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('EmpID', 'EmpName', 'user', 'Dept', 'Grade', 'Discipline', 'Active')
    list_filter = ('Active', 'Dept', 'Grade')
    search_fields = ('EmpID', 'EmpName', 'user__username', 'user__email')
    readonly_fields = ('user', 'Created_On', 'Created_Time', 'updated_at')

# --- 3. Category Admin Setup ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'created_by', 'created_on')
    list_filter = ('active', 'created_on')
    search_fields = ('name',)
    readonly_fields = ('created_on', 'created_time', 'created_by') 
    
    # Logic to automatically set created_by
    def save_model(self, request, obj, form, change):
        if not obj.pk: 
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# --- 4. SubCategory Admin Setup ---
@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'active', 'created_by')
    list_filter = ('category', 'active') 
    search_fields = ('name', 'category__name') 
    readonly_fields = ('created_on', 'created_time', 'created_by')

    # Logic to automatically set created_by
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# --- 5. Incident Admin Setup ---
@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_number', 'description', 'empID', 'catID', 'subcatID', 'status', 'priority', 'created_on')
    list_filter = ('status', 'priority', 'catID', 'created_on')
    search_fields = ('incident_number', 'description', 'empID__EmpName')
    date_hierarchy = 'created_on'
    
    fieldsets = (
        ('Incident Status', {
            'fields': (('incident_number', 'status', 'priority'), 'assigned_to', 'state'),
        }),
        ('Classification & Reporter', {
            'fields': (('catID', 'subcatID'), 'configuration_item', 'empID'),
        }),
        ('Issue Content', {
            'fields': ('subsidiary', 'description', 'impact', 'file_upload'),
        }),
        ('Timestamps', {
            'fields': (('created_on', 'created_time'), ('resolved_on', 'resolved_time')),
            'classes': ('collapse',),
        }),
    )
    # Ensure fields populated by the system or form are read-only in the Admin
    readonly_fields = ('incident_number', 'created_on', 'created_time', 'created_by', 'empID')