from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import os
import uuid
from django.utils import timezone
from django.conf import settings
from datetime import timedelta

# --- Validator ---
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.pdf']:
        raise ValidationError("File must be a JPG or PDF.")

# --- 1. Master Data for CIL ---

class Subsidiary(models.Model):
    name = models.CharField(max_length=200) 
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Department(models.Model):
    name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Grade(models.Model):
    name = models.CharField(max_length=200) 
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Discipline(models.Model):
    name = models.CharField(max_length=200) 
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

# --- 2. Custom User Model ---

class CustomUser(AbstractUser):
    USER_ROLES = (
        ('USER', 'Standard User'),
        ('IT_SUPPORT', 'IT Support Team'),
        ('ADMIN', 'Administrator'),
    )
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    role = models.CharField(max_length=15, choices=USER_ROLES, default='USER')
    EmpID = models.CharField(max_length=10, unique=True, blank=True, null=True, editable=False)
    
    Subsidiary = models.ForeignKey(Subsidiary, on_delete=models.SET_NULL, null=True, blank=True)
    Dept = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    Grade = models.ForeignKey(Grade, on_delete=models.SET_NULL, null=True, blank=True)
    Discipline = models.ForeignKey(Discipline, on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True) 
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    Gender = models.CharField(max_length=10, choices=[('Male', 'Male'), ('Female', 'Female')], blank=True, null=True)
    Floor = models.CharField(max_length=100, blank=True, null=True)
    Created_On = models.DateField(auto_now_add=True) 
    Created_Time = models.TimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    address = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.EmpID:
            last_user = CustomUser.objects.all().order_by('id').last()
            new_id = (last_user.id + 1) if last_user and last_user.id else 1
            self.EmpID = f"CIL-{str(new_id).zfill(4)}"
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.EmpID} - {self.email}"

# --- 3. ITSM Master Data ---

class RootCauseCat(models.Model):
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class RcSubcat(models.Model):
    rc_catID = models.ForeignKey(RootCauseCat, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='categories_created')
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True) 
    def __str__(self): return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    rc_cat = models.ForeignKey(RootCauseCat, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='subcategories_created')
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True) 
    def __str__(self): return f"{self.category.name} - {self.name}"
    class Meta: unique_together = ('category', 'name')

class Impact(models.Model):
    name = models.CharField(max_length=50, unique=True)
    active = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)
    def __str__(self): return self.name

# --- 4. Incident Management ---

class Incident(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'), ('IN_PROGRESS', 'In Progress'),
        ('AWAITING_FEEDBACK', 'Resolved - Awaiting User Feedback'),
        ('REOPENED', 'Reopened by User'), ('CLOSED', 'Closed'),
    ]
    PRIORITY_CHOICES = [('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
    
    incident_number = models.CharField(max_length=50, unique=True)
    subsidiary = models.ForeignKey(Subsidiary, on_delete=models.SET_NULL, null=True, blank=True)
    empID = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents_reported')
    catID = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcatID = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    configuration_item = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    file_upload = models.FileField(upload_to='incidents/', blank=True, null=True, validators=[validate_file_extension])
    impact = models.ForeignKey(Impact, on_delete=models.PROTECT)
    state = models.CharField(max_length=50, default='Open')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    def save(self, *args, **kwargs):
        if not self.incident_number:
            self.incident_number = f"INC-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.incident_number} - {self.status}"

class TicketFeedback(models.Model):
    FEEDBACK_CHOICES = ((True, 'Yes (Satisfied)'), (False, 'No (Not Satisfied/Reopen)'),)
    ticket = models.ForeignKey(Incident, related_name='feedback_history', on_delete=models.CASCADE)
    is_satisfied = models.BooleanField(choices=FEEDBACK_CHOICES, default=True) 
    comments = models.TextField(null=True, blank=True)
    provided_at = models.DateTimeField(auto_now_add=True)
    provided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='feedback_given')

    class Meta:
        ordering = ['-provided_at']
        verbose_name_plural = "Ticket Feedback"
    
    def __str__(self):
        satisfaction = "Satisfied" if self.is_satisfied else "Reopened"
        return f'Feedback for {self.ticket.incident_number}: {satisfaction}'

class IncidentTracking(models.Model):
    incident = models.OneToOneField(Incident, on_delete=models.CASCADE, related_name='tracking')
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=50)
    assigned_to = models.CharField(max_length=100, blank=True, null=True)
    feedback_action = models.BooleanField(default=False)
    resolved_on = models.DateField(null=True, blank=True)
    resolved_time = models.TimeField(null=True, blank=True)
    delays = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.resolved_on and self.created_on:
            self.delays = (self.resolved_on - self.created_on).days
        super().save(*args, **kwargs)

    def __str__(self): return f"Tracking for {self.incident.incident_number}"

# --- 5. Support Modules ---

class LoginMonitor(models.Model):
    login_by = models.CharField(max_length=100)
    login_date = models.DateField(auto_now_add=True)
    login_time = models.TimeField(auto_now_add=True)
    logout_date = models.DateField(null=True, blank=True)
    logout_time = models.TimeField(null=True, blank=True)
    mac_address = models.CharField(max_length=200, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    session_key = models.CharField(max_length=100, null=True, blank=True)

class SLAManagement(models.Model):
    incident = models.OneToOneField(Incident, on_delete=models.CASCADE, related_name='sla')
    response_due = models.DateTimeField() 
    resolution_due = models.DateTimeField() 
    responded_on = models.DateTimeField(null=True, blank=True) 
    resolved_on = models.DateTimeField(null=True, blank=True) 
    sla_status = models.CharField(max_length=50, default='Within SLA')
    breach_reason = models.TextField(blank=True, null=True)

class Asset(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    custodian = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assets')
    admin_owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='owned_assets')
    status = models.CharField(max_length=100, default='In Use')
    serial_number = models.CharField(max_length=200, unique=True)
    purchase_date = models.DateField()
    warranty_expiry = models.DateField()
    software_version = models.IntegerField(default=1)
    last_audit_date = models.DateField()


class ProblemManagement(models.Model):
    description = models.TextField()
    root_cause_catID = models.ForeignKey(RootCauseCat, on_delete=models.SET_NULL, null=True)
    root_cause_subCatID = models.ForeignKey(RcSubcat, on_delete=models.SET_NULL, null=True)
    root_cause = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('open', 'Open'), ('close', 'Closed'), ('in_progress', 'In Progress')], default='open')
    known_issue = models.BooleanField(default=False)
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True)
    resolved_on = models.DateField(null=True, blank=True)
    resolved_time = models.TimeField(null=True, blank=True)
    delays = models.IntegerField(null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_problems')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_problems')

    def save(self, *args, **kwargs):
        if self.resolved_on and self.created_on:
            self.delays = (self.resolved_on - self.created_on).days
        super().save(*args, **kwargs)

class ProblemCase(models.Model):
    name = models.CharField(max_length=200)
    rc_catID = models.ForeignKey(RootCauseCat, on_delete=models.CASCADE)
    freq_count = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    detected_on = models.DateField(null=True, blank=True)
    threshold_limit = models.IntegerField(default=5)
    time_window_hours = models.IntegerField(default=24)

class ServiceRequest(models.Model):
    catID = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcatID = models.ForeignKey(SubCategory, on_delete=models.CASCADE)
    empID = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='OPEN')








class Vendor(models.Model):
    # Vendor_ID is PK
    vendor_name = models.CharField(max_length=100) #
    contact_person = models.CharField(max_length=100) #
    support_email = models.EmailField(max_length=100) #
    support_phone = models.CharField(max_length=100) #
    sla_agreement = models.TextField(max_length=500) # As discussed: varchar/text
    contract_expiry = models.DateField() #
    asset_category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True) # FK
    account_number = models.IntegerField() #
    status = models.CharField(max_length=50, default='Active') #

    def __str__(self): return self.vendor_name

class SecurityManagement(models.Model):
    # Security_ID is PK
    threat_type = models.CharField(max_length=100) #
    severity = models.CharField(max_length=100) #
    affected_asset = models.ForeignKey('Asset', on_delete=models.CASCADE) # FK
    assigned_admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True) # FK
    status = models.CharField(max_length=50, default='Detected') #
    detected_on = models.DateField(auto_now_add=True) #
    detected_time = models.TimeField(auto_now_add=True) #
    resolved_on = models.DateField(null=True, blank=True) #
    resolved_time = models.TimeField(null=True, blank=True) #

class BackupManagement(models.Model):
    # Backup_ID is PK
    target_asset = models.ForeignKey('Asset', on_delete=models.CASCADE) # FK
    backup_type = models.CharField(max_length=100) # Full/Incremental
    storage_location = models.CharField(max_length=100) #
    last_success_date = models.DateField(null=True, blank=True) #
    next_schedule = models.DateField() #
    status = models.CharField(max_length=50, default='Scheduled') #

class AuditManagement(models.Model):
    # Audit_ID is PK
    timestamp = models.DateTimeField(auto_now_add=True) #
    performed_by = models.CharField(max_length=100) #
    action_type = models.CharField(max_length=100) # Update/Delete/Create
    old_value = models.TextField(null=True, blank=True) #
    new_value = models.TextField(null=True, blank=True) #


class KnowledgeBase(models.Model):
    topic = models.CharField(max_length=200)
    content = models.TextField() # This contains the "how-to" guide
    category = models.CharField(max_length=100) # Hardware, Software, etc.

    def __str__(self):
        return self.topic