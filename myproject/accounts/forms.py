# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError 
from .models import Incident, Category, SubCategory, CustomUser, TicketFeedback

User = get_user_model() 

# =====================================================================
# 1. EMPLOYEE & PROFILE FORMS (Existing Code)
# =====================================================================

class EmployeeRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User 
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 
            'date_of_birth', 'EmpID', 'Gender', 'Dept', 'Grade', 
            'Discipline', 'Floor', 'Active'
        ]

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        emp_id = cleaned_data.get('EmpID')
        
        # NOTE: Your existing clean method is good for checking uniqueness
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email address already exists.")
        if emp_id and User.objects.filter(EmpID=emp_id).exists():
            self.add_error('EmpID', "This Employee ID already exists. Please choose another.")

        return cleaned_data

    @transaction.atomic 
    def save(self, commit=True):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        first_name = self.cleaned_data.get('first_name', '')
        last_name = self.cleaned_data.get('last_name', '')
        
        if not email or not password:
            raise ValidationError("Email and Password are required fields.")
            
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        custom_fields = [
            'EmpID', 'phone_number', 'date_of_birth', 'Gender', 
            'Dept', 'Grade', 'Discipline', 'Floor', 'Active', 'role' # Include role for assignment later
        ]
        
        for field in custom_fields:
            if field in self.cleaned_data:
                setattr(user, field, self.cleaned_data[field])
        
        # Set default role upon registration
        setattr(user, 'role', 'USER')
        
        if commit:
            user.save() 
            
        return user


class ProfileCompletionForm(forms.ModelForm):
    class Meta:
        model = User 
        fields = [
            'first_name', 'last_name', 'EmpID', 'email', 'phone_number', 
            'date_of_birth', 'Gender', 'Dept', 'Grade', 'Discipline', 'Floor'
        ]

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
        
# =====================================================================
# 2. INCIDENT CREATION FORM (Existing Code)
# =====================================================================

class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            'subsidiary', 'catID', 'subcatID', 'description', 
            'file_upload', 'impact', 'priority' # Added priority for user input
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super(IncidentForm, self).__init__(*args, **kwargs)
        
        # Initializing subcategory queryset for dependency logic
        self.fields['subcatID'].queryset = SubCategory.objects.none()

        if 'catID' in self.data:
            try:
                category_id = int(self.data.get('catID'))
                self.fields['subcatID'].queryset = SubCategory.objects.filter(category_id=category_id, active=True)
            except (ValueError, TypeError):
                pass

# =====================================================================
# 3. WORKFLOW FORMS (NEW INTEGRATION)
# =====================================================================

class ResolutionForm(forms.Form):
    """
    Form used by IT Support to submit resolution notes before sending to user.
    """
    resolution_notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed steps and solution used to resolve the issue...'}),
        label="Resolution Notes"
    )

    def clean_resolution_notes(self):
        notes = self.cleaned_data.get('resolution_notes')
        if not notes:
            raise forms.ValidationError("Resolution notes are required to close the ticket.")
        return notes


class FeedbackForm(forms.Form):
    """
    Form used by the End User to submit satisfaction (Yes/No) and comments.
    """
    is_satisfied = forms.ChoiceField(
        choices=TicketFeedback.FEEDBACK_CHOICES,
        widget=forms.RadioSelect,
        label="Are you satisfied with the resolution?"
    )
    comments = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional comments...'}),
        required=False,
        label="Comments"
    )