from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError 
from .models import Incident, Category, SubCategory, CustomUser, TicketFeedback, Subsidiary, Department, Grade, Discipline,ProblemManagement, Asset
from .models import ServiceRequest
User = get_user_model() 

# =====================================================================
# 1. EMPLOYEE & PROFILE FORMS (Updated for CIL Dropdowns)
# =====================================================================

class EmployeeRegistrationForm(forms.ModelForm):
    # Password fields with confirm logic
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))

    class Meta:
        model = User 
        # Removed 'EmpID' (auto-gen) and 'Active' (auto-set)
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'date_of_birth', 'Gender', 'Subsidiary', 'Dept', 'Grade', 
            'Discipline', 'Floor', 'password', 'confirm_password'
        ]
        # Applying Bootstrap classes to the dropdowns and inputs
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'Gender': forms.Select(attrs={'class': 'form-control'}),
            'Subsidiary': forms.Select(attrs={'class': 'form-control'}),
            'Dept': forms.Select(attrs={'class': 'form-control'}),
            'Grade': forms.Select(attrs={'class': 'form-control'}),
            'Discipline': forms.Select(attrs={'class': 'form-control'}),
            'Floor': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        
        # Email Uniqueness check
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email address already exists.")
        
        # Password Match check
        if password != confirm_password:
            raise ValidationError("Passwords do not match.")

        return cleaned_data

    @transaction.atomic 
    def save(self, commit=True):
        user = super().save(commit=False)
        # Handle password encryption
        user.set_password(self.cleaned_data["password"])
        # Use email as username since we removed username field from UI
        user.username = self.cleaned_data["email"]
        # Automatically set user as active
        user.is_active = True 
        # Set default role
        user.role = 'USER'
        
        if commit:
            user.save() # This triggers the auto-sequential EmpID in models.py
            
        return user

# =====================================================================
# 2. PROFILE COMPLETION FORM (Cleaned)
# =====================================================================

class ProfileCompletionForm(forms.ModelForm):
    class Meta:
        model = User 
        fields = [
            'first_name', 'last_name', 'phone_number', 
            'date_of_birth', 'Gender', 'Subsidiary', 'Dept', 'Grade', 'Discipline', 'Floor'
        ]
        widgets = {f: forms.Select(attrs={'class': 'form-control'}) for f in ['Gender', 'Subsidiary', 'Dept', 'Grade', 'Discipline']}

# =====================================================================
# 3. INCIDENT & WORKFLOW FORMS (Remaining Code)
# =====================================================================

class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        # 'subsidiary' is now included as a ForeignKey-backed field
        fields = [
            'subsidiary', 'catID', 'subcatID', 'description', 
            'file_upload', 'impact', 'priority'
        ]
        widgets = {
            'subsidiary': forms.Select(attrs={'class': 'form-control'}),
            'catID': forms.Select(attrs={'class': 'form-control'}),
            'subcatID': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'impact': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(IncidentForm, self).__init__(*args, **kwargs)
        
        # This keeps your dynamic Category-SubCategory logic working
        self.fields['subcatID'].queryset = SubCategory.objects.none()

        if 'catID' in self.data:
            try:
                category_id = int(self.data.get('catID'))
                self.fields['subcatID'].queryset = SubCategory.objects.filter(
                    category_id=category_id, 
                    active=True
                )
            except (ValueError, TypeError):
                pass
class FeedbackForm(forms.Form):
    is_satisfied = forms.ChoiceField(
        choices=TicketFeedback.FEEDBACK_CHOICES,
        widget=forms.RadioSelect,
        label="Are you satisfied with the resolution?"
    )
    comments = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False
    )

class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest
        fields = ['catID', 'subcatID', 'description']
        widgets = {
            'catID': forms.Select(attrs={'class': 'form-control'}),
            'subcatID': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Need new laptop battery'}),
        }



class ProblemManagementForm(forms.ModelForm):
    """Form to document root cause and status of recurring issues"""
    class Meta:
        model = ProblemManagement
        fields = ['description', 'root_cause_catID', 'root_cause_subCatID', 'root_cause', 'status', 'known_issue', 'assigned_to']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'root_cause': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'root_cause_catID': forms.Select(attrs={'class': 'form-select'}),
        }

class AssetSearchForm(forms.Form):
    """Form to filter assets by serial number or custodian"""
    query = forms.CharField(
        required=False, 
        label='Search Assets',
        widget=forms.TextInput(attrs={'placeholder': 'Serial Number or Custodian...', 'class': 'form-control'})
    )

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        # Include the fields you took during registration
        fields = ['first_name', 'last_name', 'email', 'phone_number'] 
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }