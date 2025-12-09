from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
import os
import uuid
from django.utils import timezone

# Function to validate the file extension
def validate_file_extension(value):
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.pdf']:
        raise ValidationError("File must be a JPG or PDF.")

# Custom User model extending AbstractUser
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.username

# --- Employee model to store employee details ---
class Employee(models.Model):
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    EmpID = models.CharField(max_length=10, unique=True, blank=True, null=True)
    EmpName = models.CharField(max_length=100, blank=True, null=True)
    DoB = models.DateField(blank=True, null=True)
    Gender = models.CharField(max_length=6, choices=GENDER_CHOICES, blank=True, null=True)
    Dept = models.CharField(max_length=100, blank=True, null=True)
    Grade = models.CharField(max_length=50, blank=True, null=True)
    Discipline = models.CharField(max_length=100, blank=True, null=True)
    Floor = models.CharField(max_length=100, blank=True, null=True)
    Active = models.BooleanField(default=True)
    Created_On = models.DateField(auto_now_add=True)
    Created_Time = models.TimeField(auto_now_add=True)  # Removed default option
    updated_at = models.DateTimeField(auto_now=True)
    Email = models.EmailField(max_length=100, blank=True, null=True)
    Phone = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.EmpName or f"Profile for {self.user.username}"

# --- Category model for incident classification ---
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, related_name='categories_created')
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True)  # Removed default option

    def __str__(self):
        return self.name

# --- SubCategory model for further incident classification ---
class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, related_name='subcategories_created')
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True)  # Removed default option

    def __str__(self):
        return f"{self.category.name} - {self.name}"

    class Meta:
        unique_together = ('category', 'name')

# --- Incident model for managing incidents ---
class Incident(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    incident_number = models.CharField(max_length=50, unique=True)
    subsidiary = models.CharField(max_length=100, blank=True, null=True) 
    empID = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True)
    catID = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcatID = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    configuration_item = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    file_upload = models.FileField(upload_to='incidents/', blank=True, null=True, validators=[validate_file_extension])
    impact = models.CharField(max_length=50)
    state = models.CharField(max_length=50, default='Open')
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True)
    created_on = models.DateField(auto_now_add=True)
    created_time = models.TimeField(auto_now_add=True)  # Removed default option
    assigned_to = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_incidents')
    resolved_on = models.DateField(null=True, blank=True)
    resolved_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    def save(self, *args, **kwargs):
        if not self.incident_number:
            self.incident_number = f"INC-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"INC-{self.incident_number} - {self.status}"
