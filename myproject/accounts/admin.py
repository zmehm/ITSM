from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Category, SubCategory, Incident 

# --- 1. CustomUser Admin Setup ---
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'EmpID', 'Dept', 'Grade', 'is_staff', 'is_active'
    )
    
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Profile Details', {'fields': (
            'EmpID', 'Gender', 'Dept', 'Grade', 'Discipline', 'Floor', 'Active',
            'phone_number', 'date_of_birth', 'address'
        )}), 
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Profile Details', {'fields': (
            'EmpID', 'Gender', 'Dept', 'Grade', 'Discipline', 'Floor', 'Active',
            'phone_number', 'date_of_birth', 'address'
        )}),
    )

admin.site.register(CustomUser, CustomUserAdmin)

# --- 2. Category/SubCategory Inline Setup ---
class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'active', 'created_by', 'created_on')
    list_filter = ('active', 'created_on')
    search_fields = ('name',)
    readonly_fields = ('created_on', 'created_time', 'created_by') 
    inlines = [SubCategoryInline]

    def save_model(self, request, obj, form, change):
        if not obj.pk: 
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'active', 'created_by')
    list_filter = ('category', 'active') 
    search_fields = ('name', 'category__name') 
    readonly_fields = ('created_on', 'created_time', 'created_by')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

# --- 3. Incident Admin Setup ---
@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_number', 'description', 'get_emp_name', 'catID', 'subcatID', 'status', 'priority', 'created_on')
    list_filter = ('status', 'priority', 'catID', 'created_on')
    search_fields = ('incident_number', 'description', 'empID__first_name', 'empID__last_name')
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

    readonly_fields = ('incident_number', 'created_on', 'created_time', 'created_by')

    @admin.display(description='Reporter Name')
    def get_emp_name(self, obj):
        if obj.empID:
            return f"{obj.empID.first_name} {obj.empID.last_name} ({obj.empID.EmpID or 'N/A'})"
        return "N/A"