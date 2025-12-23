from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Category, SubCategory, Incident, 
    Subsidiary, Department, Grade, Discipline, Impact,
    IncidentTracking, ServiceRequest, LoginMonitor, 
    Asset, SLAManagement, RootCauseCat, RcSubcat, 
    ProblemManagement, ProblemCase, TicketFeedback,Vendor, SecurityManagement, BackupManagement, AuditManagement,
    KnowledgeBase
)

# --- 1. Master Data Registration ---
admin.site.register(Subsidiary)
admin.site.register(Department)
admin.site.register(Grade)
admin.site.register(Discipline)
admin.site.register(Impact)
admin.site.register(RootCauseCat)
admin.site.register(RcSubcat)

# --- 2. CustomUser Admin Setup ---
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    
    list_display = (
        'EmpID', 'email', 'first_name', 'last_name', 
        'role', 'Dept', 'is_active'
    )
    
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Profile Details', {'fields': (
            'EmpID', 'role', 'Gender', 'Subsidiary', 'Dept', 
            'Grade', 'Discipline', 'Floor', 'phone_number'
        )}), 
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Employee Profile Details', {'fields': (
            'role', 'Gender', 'Subsidiary', 'Dept', 
            'Grade', 'Discipline', 'Floor'
        )}),
    )

    readonly_fields = ('EmpID',)

admin.site.register(CustomUser, CustomUserAdmin)

# --- 3. Category/SubCategory Inline Setup ---
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

# --- 4. Incident Tracking & Monitoring Setup ---
@admin.register(IncidentTracking)
class IncidentTrackingAdmin(admin.ModelAdmin):
    """Admin interface for the separate monitoring database"""
    list_display = (
        'incident', 'status', 'assigned_to', 
        'created_on', 'resolved_on', 'delays'
    )
    list_filter = ('status', 'created_on', 'resolved_on')
    search_fields = ('incident__incident_number', 'assigned_to')
    
    readonly_fields = (
        'incident', 'created_on', 'created_time', 
        'created_by', 'delays'
    )

# --- 5. Service Request Admin Setup ---
@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    """Admin interface for Service Requests as per Excel sheet"""
    list_display = ('id', 'empID', 'catID', 'subcatID', 'status', 'created_at')
    list_filter = ('status', 'catID', 'created_at')
    search_fields = ('empID__email', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Request Info', {
            'fields': ('empID', 'status')
        }),
        ('Classification', {
            'fields': ('catID', 'subcatID', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at',),
        }),
    )

# --- 6. Incident Admin Setup ---
@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        'incident_number', 'get_emp_name', 'catID', 
        'subcatID', 'status', 'priority', 'created_on', 'subsidiary'
    )
    list_filter = ('status', 'priority', 'catID', 'created_on')
    search_fields = (
        'incident_number', 'description', 
        'empID__first_name', 'empID__last_name'
    )
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
            'fields': (('created_on', 'created_time'), ('resolved_at', 'resolved_date')),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('incident_number', 'created_on', 'created_time', 'created_by')

    @admin.display(description='Reporter Name')
    def get_emp_name(self, obj):
        if obj.empID:
            return f"{obj.empID.first_name} {obj.empID.last_name} ({obj.empID.EmpID or 'N/A'})"
        return "N/A"

# --- 7. Login Monitor & Feedback ---
@admin.register(LoginMonitor)
class LoginMonitorAdmin(admin.ModelAdmin):
    """Audits user sessions and network identifiers"""
    list_display = ('login_by', 'login_date', 'login_time', 'logout_date', 'logout_time', 'ip_address')
    list_filter = ('login_date', 'login_by')
    readonly_fields = ('login_date', 'login_time', 'ip_address', 'mac_address')

@admin.register(TicketFeedback)
class TicketFeedbackAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'is_satisfied', 'provided_by', 'provided_at')
    list_filter = ('is_satisfied',)

# --- 8. SLA & Asset Management (NEW) ---
@admin.register(SLAManagement)
class SLAAdmin(admin.ModelAdmin):
    """Tracks restoration deadlines and breach reasons"""
    list_display = ('incident', 'sla_status', 'response_due', 'resolution_due', 'breach_reason')
    list_filter = ('sla_status', 'response_due', 'resolution_due')
    search_fields = ('incident__incident_number', 'breach_reason')

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Manages company hardware and audit compliance"""
    list_display = ('name', 'serial_number', 'custodian', 'status', 'warranty_expiry', 'last_audit_date')
    search_fields = ('name', 'serial_number', 'custodian__email')
    list_filter = ('status', 'category', 'last_audit_date')

# --- 9. Problem Management (NEW) ---
@admin.register(ProblemManagement)
class ProblemManagementAdmin(admin.ModelAdmin):
    """Root cause analysis for recurring incidents"""
    list_display = ('id', 'description', 'status', 'root_cause_catID', 'known_issue', 'delays')
    list_filter = ('status', 'known_issue', 'root_cause_catID')
    readonly_fields = ('created_on', 'created_time', 'delays')

@admin.register(ProblemCase)
class ProblemCaseAdmin(admin.ModelAdmin):
    """Monitors patterns of frequent failures"""
    list_display = ('name', 'rc_catID', 'freq_count', 'active', 'detected_on')
    list_filter = ('active', 'rc_catID')




@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Manages external service providers and contracts"""
    list_display = ('vendor_name', 'contact_person', 'support_email', 'contract_expiry', 'status')
    list_filter = ('status', 'asset_category')
    search_fields = ('vendor_name', 'support_email', 'account_number')

@admin.register(SecurityManagement)
class SecurityAdmin(admin.ModelAdmin):
    """Tracks system threats and resolution status"""
    list_display = ('threat_type', 'severity', 'affected_asset', 'status', 'detected_on')
    list_filter = ('severity', 'status')
    readonly_fields = ('detected_on', 'detected_time')

@admin.register(BackupManagement)
class BackupAdmin(admin.ModelAdmin):
    """Monitors data safety and backup schedules"""
    list_display = ('target_asset', 'backup_type', 'last_success_date', 'next_schedule', 'status')
    list_filter = ('status', 'backup_type')

@admin.register(AuditManagement)
class AuditAdmin(admin.ModelAdmin):
    """Immutable log of administrative actions"""
    list_display = ('timestamp', 'performed_by', 'action_type')
    readonly_fields = ('timestamp', 'performed_by', 'action_type', 'old_value', 'new_value')
    # Audits should generally be read-only to ensure integrity

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('topic', 'category')
    search_fields = ('topic', 'content')