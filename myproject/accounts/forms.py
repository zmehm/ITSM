# accounts/forms.py

from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.core.exceptions import ValidationError 
from .models import Incident, Category, SubCategory, CustomUser 

User = get_user_model() 
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
            'Dept', 'Grade', 'Discipline', 'Floor', 'Active'
        ]
        
        for field in custom_fields:
            if field in self.cleaned_data:
                setattr(user, field, self.cleaned_data[field])

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
        

class IncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = [
            'subsidiary', 'catID', 'subcatID', 'description', 'file_upload', 'impact', 'state'
        ]

    def __init__(self, *args, **kwargs):
        super(IncidentForm, self).__init__(*args, **kwargs)
        self.fields['subcatID'].queryset = SubCategory.objects.none()

        if 'catID' in self.data:
            try:
                category_id = int(self.data.get('catID'))
                self.fields['subcatID'].queryset = SubCategory.objects.filter(category_id=category_id)
            except (ValueError, TypeError):
                pass