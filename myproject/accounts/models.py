# accounts/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import os
import uuid
from django.utils import timezone
from django.conf import settings # Import settings for user model reference

def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.pdf']:
        raise ValidationError("File must be a JPG or PDF.")

# --- 1. CustomUser Model (Integrated with Roles) ---

# Define Role Choices (Integrated directly into CustomUser)
USER_ROLES = (
    ('USER', 'Standard User'),
    ('IT_SUPPORT', 'IT Support Team'),
    ('ADMIN', 'Administrator'),
)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email' 
    REQUIRED_FIELDS = ['first_name', 'last_name', 'EmpID', 'username']

    # --- ROLE FIELD ADDED ---
    role = models.CharField(
        max_length=15,
        choices=USER_ROLES,
        default='USER'
    )
    # ------------------------

    # Choices for Gender
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    # --- EXISTING FIELDS ---
    EmpID = models.CharField(max_length=10, unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    Gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True, null=True)
    Dept = models.CharField(max_length=100, blank=True, null=True)
    Grade = models.CharField(max_length=50, blank=True, null=True)
    Discipline = models.CharField(max_length=100, blank=True, null=True)
    Floor = models.CharField(max_length=100, blank=True, null=True)
    Active = models.BooleanField(default=True)
    
    # Tracking fields
    Created_On = models.DateField(auto_now_add=True) 
    Created_Time = models.TimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.username
        
    @property
    def is_support(self):
        return self.role == 'IT_SUPPORT'

    @property
    def is_admin(self):
        return self.role == 'ADMIN'


# --- 2. Category and SubCategory Models (Unchanged) ---

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='categories_created')
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True) 

    def __str__(self):
        return self.name

class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='subcategories_created')
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    class Meta:
        unique_together = ('category', 'name')

# --- 3. Incident Model (Updated Status Choices) ---

class Incident(models.Model):
    # UPDATED STATUS CHOICES for workflow integration
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('IN_PROGRESS', 'In Progress'),
        ('AWAITING_FEEDBACK', 'Resolved - Awaiting User Feedback'), # NEW STATE
        ('REOPENED', 'Reopened by User'),                           # NEW STATE
        ('CLOSED', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    incident_number = models.CharField(max_length=50, unique=True)
    subsidiary = models.CharField(max_length=100, blank=True, null=True) 
    
    # Using settings.AUTH_USER_MODEL for FKs
    empID = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='incidents_reported') 
    catID = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcatID = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    configuration_item = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    file_upload = models.FileField(upload_to='incidents/', blank=True, null=True, validators=[validate_file_extension])
    impact = models.CharField(max_length=50)
    state = models.CharField(max_length=50, default='Open') # Redundant with 'status', but kept for compatibility
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    resolved_on = models.DateField(null=True, blank=True)
    resolved_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW') # Default changed to 'NEW' (uppercase)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    def save(self, *args, **kwargs):
        if not self.incident_number:
            self.incident_number = f"INC-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"INC-{self.incident_number} - {self.status}"
        
# --- 4. TicketFeedback Model (New Integration) ---

class TicketFeedback(models.Model):
    """
    Stores user satisfaction feedback for a resolved ticket.
    """
    FEEDBACK_CHOICES = (
        (True, 'Yes (Satisfied)'),
        (False, 'No (Not Satisfied/Reopen)'),
    )
    
    ticket = models.ForeignKey(
        Incident, 
        related_name='feedback_history', 
        on_delete=models.CASCADE
    )
    
    # True means satisfied (closes ticket), False means dissatisfied (reopens ticket)
    is_satisfied = models.BooleanField(
        choices=FEEDBACK_CHOICES,
        default=True
    ) 
    
    comments = models.TextField(null=True, blank=True)
    
    provided_at = models.DateTimeField(auto_now_add=True)
    provided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='feedback_given')

    class Meta:
        ordering = ['-provided_at']
        verbose_name_plural = "Ticket Feedback"
    
    def __str__(self):
        satisfaction = "Satisfied" if self.is_satisfied else "Reopened"
        return f'Feedback for {self.ticket.incident_number}: {satisfaction}'